import json
import unicodedata

from django.db import migrations, models

UNICODE_VERSION = "15.0.0"
LOWER_MAPPING_COUNT = 1433
CASED_COUNT = 4526
CASE_IGNORABLE_COUNT = 2707
CASE_IGNORABLE_EXTRA = {
    # Unicode 15.0 Word_Break MidLetter, MidNumLet, and Single_Quote values
    # whose General_Category is outside Mn, Me, Cf, Lm, and Sk.
    0x0027,
    0x002E,
    0x003A,
    0x00B7,
    0x0387,
    0x055F,
    0x05F4,
    0x2018,
    0x2019,
    0x2024,
    0x2027,
    0xFE13,
    0xFE52,
    0xFE55,
    0xFF07,
    0xFF0E,
    0xFF1A,
}
WHITESPACE_CODEPOINTS = (
    0x0009,
    0x000A,
    0x000B,
    0x000C,
    0x000D,
    0x001C,
    0x001D,
    0x001E,
    0x001F,
    0x0020,
    0x0085,
    0x00A0,
    0x1680,
    0x2000,
    0x2001,
    0x2002,
    0x2003,
    0x2004,
    0x2005,
    0x2006,
    0x2007,
    0x2008,
    0x2009,
    0x200A,
    0x2028,
    0x2029,
    0x202F,
    0x205F,
    0x3000,
)


def _tables():
    if unicodedata.unidata_version != UNICODE_VERSION:
        raise RuntimeError(
            "Login ID migration requires Python Unicode " + UNICODE_VERSION
        )

    lower = {}
    cased = {}
    case_ignorable = {}
    for codepoint in range(0x110000):
        if 0xD800 <= codepoint <= 0xDFFF:
            continue
        character = chr(codepoint)
        lowered = character.lower()
        if lowered != character:
            lower[character] = lowered
        if (
            character.islower()
            or character.isupper()
            or unicodedata.category(character) == "Lt"
        ):
            cased[character] = True
        if (
            unicodedata.category(character) in {"Mn", "Me", "Cf", "Lm", "Sk"}
            or codepoint in CASE_IGNORABLE_EXTRA
        ):
            case_ignorable[character] = True

    whitespace = tuple(
        codepoint for codepoint in range(0x110000) if chr(codepoint).isspace()
    )
    if (
        len(lower) != LOWER_MAPPING_COUNT
        or len(cased) != CASED_COUNT
        or len(case_ignorable) != CASE_IGNORABLE_COUNT
        or whitespace != WHITESPACE_CODEPOINTS
    ):
        raise RuntimeError(
            "Python Unicode tables do not match the locked Login ID policy"
        )
    return lower, cased, case_ignorable


def preflight_existing_login_ids(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        raise RuntimeError("Canonical Login ID migration requires PostgreSQL")
    _tables()
    User = apps.get_model("accounts", "User")
    user_table = schema_editor.connection.ops.quote_name(User._meta.db_table)
    # The migration is atomic on PostgreSQL. Hold this lock from before the
    # preflight scan through trigger installation so a concurrent insert or
    # Login ID update cannot create a noncanonical value in the gap.
    schema_editor.execute(f"LOCK TABLE {user_table} IN SHARE ROW EXCLUSIVE MODE")
    seen = set()
    noncanonical = 0
    collisions = 0
    for login_id in (
        User.objects.using(schema_editor.connection.alias)
        .values_list("login_id", flat=True)
        .iterator(chunk_size=2000)
    ):
        canonical = login_id.strip().lower()
        if not canonical or len(canonical) > 150 or canonical != login_id:
            noncanonical += 1
        if canonical in seen:
            collisions += 1
        seen.add(canonical)
    if noncanonical or collisions:
        raise RuntimeError(
            "Canonical Login ID migration stopped without changing accounts: "
            f"{noncanonical} noncanonical and {collisions} canonical collision(s) "
            "need an explicit reviewed UUID-to-login mapping. No identifiers were logged."
        )


def install_login_id_database_policy(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        raise RuntimeError("Canonical Login ID migration requires PostgreSQL")
    lower, cased, case_ignorable = _tables()
    lower_json = json.dumps(lower, ensure_ascii=True, separators=(",", ":"))
    cased_json = json.dumps(cased, ensure_ascii=True, separators=(",", ":"))
    case_ignorable_json = json.dumps(
        case_ignorable, ensure_ascii=True, separators=(",", ":")
    )
    trim_characters = " || ".join(
        f"chr({codepoint})" for codepoint in WHITESPACE_CODEPOINTS
    )
    user_table = connection.ops.quote_name(
        apps.get_model("accounts", "User")._meta.db_table
    )
    schema_editor.execute(
        f"""
        CREATE FUNCTION virms_canonical_login_id(input text)
        RETURNS text
        LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE
        AS $virms_login_canonicalizer$
        DECLARE
            normalized text;
            result_text text := '';
            current_character text;
            context_character text;
            mapped_character text;
            character_position integer;
            context_position integer;
            input_length integer;
            cased_before boolean;
            cased_after boolean;
            lower_map CONSTANT jsonb := $virms_lower_map${lower_json}$virms_lower_map$::jsonb;
            cased_map CONSTANT jsonb := $virms_cased_map${cased_json}$virms_cased_map$::jsonb;
            case_ignorable_map CONSTANT jsonb := $virms_ci_map${case_ignorable_json}$virms_ci_map$::jsonb;
        BEGIN
            normalized := btrim(input, {trim_characters});
            input_length := char_length(normalized);
            IF input_length = 0 THEN
                RETURN '';
            END IF;

            FOR character_position IN 1..input_length LOOP
                current_character := substr(normalized, character_position, 1);
                IF current_character = chr(931) THEN
                    cased_before := false;
                    context_position := character_position - 1;
                    WHILE context_position > 0 LOOP
                        context_character := substr(normalized, context_position, 1);
                        IF case_ignorable_map ? context_character THEN
                            context_position := context_position - 1;
                            CONTINUE;
                        END IF;
                        cased_before := cased_map ? context_character;
                        EXIT;
                    END LOOP;

                    IF cased_before THEN
                        cased_after := false;
                        context_position := character_position + 1;
                        WHILE context_position <= input_length LOOP
                            context_character := substr(normalized, context_position, 1);
                            IF case_ignorable_map ? context_character THEN
                                context_position := context_position + 1;
                                CONTINUE;
                            END IF;
                            cased_after := cased_map ? context_character;
                            EXIT;
                        END LOOP;
                        IF NOT cased_after THEN
                            result_text := result_text || chr(962);
                            CONTINUE;
                        END IF;
                    END IF;
                END IF;

                mapped_character := lower_map ->> current_character;
                result_text := result_text || COALESCE(mapped_character, current_character);
            END LOOP;
            RETURN result_text;
        END
        $virms_login_canonicalizer$;
        """
    )
    schema_editor.execute(
        """
        CREATE FUNCTION virms_canonicalize_user_login_id() RETURNS trigger
        LANGUAGE plpgsql AS $virms_login_trigger$
        BEGIN
            NEW.login_id := virms_canonical_login_id(NEW.login_id);
            IF NEW.login_id = '' THEN
                RAISE EXCEPTION 'Login ID cannot be blank' USING ERRCODE='23514';
            END IF;
            IF char_length(NEW.login_id) > 150 THEN
                RAISE EXCEPTION 'Canonical Login ID exceeds 150 characters'
                    USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END
        $virms_login_trigger$;
        """
    )
    schema_editor.execute(
        f"""
        CREATE TRIGGER virms_canonical_user_login_id
        BEFORE INSERT OR UPDATE OF login_id ON {user_table}
        FOR EACH ROW EXECUTE FUNCTION virms_canonicalize_user_login_id();
        """
    )


def remove_login_id_database_policy(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    user_table = schema_editor.connection.ops.quote_name(
        apps.get_model("accounts", "User")._meta.db_table
    )
    schema_editor.execute(f"DROP TRIGGER virms_canonical_user_login_id ON {user_table}")
    schema_editor.execute("DROP FUNCTION virms_canonicalize_user_login_id()")
    schema_editor.execute("DROP FUNCTION virms_canonical_login_id(text)")


class Migration(migrations.Migration):
    dependencies = [("accounts", "0008_loginattempt_login_retry_after_idx")]

    operations = [
        migrations.RunPython(
            preflight_existing_login_ids,
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            install_login_id_database_policy,
            remove_login_id_database_policy,
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=~models.Q(login_id=""),
                name="account_login_id_nonempty",
            ),
        ),
    ]
