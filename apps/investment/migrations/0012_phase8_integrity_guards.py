from django.db import migrations


FORWARD_SQL = r"""
CREATE FUNCTION investment_vehicle_result_scope_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_company uuid;
    p_company uuid;
    p_vehicle uuid;
    p_investor uuid;
    s_company uuid;
    s_vehicle uuid;
    i_company uuid;
    vr_company uuid;
    vr_module text;
    ir_company uuid;
    ir_module text;
BEGIN
    SELECT tenant_id INTO v_company FROM vehicles_vehicle WHERE id = NEW.vehicle_id;
    SELECT tenant_id, vehicle_id, investor_id INTO p_company, p_vehicle, p_investor
      FROM vehicles_vehiclepurchase WHERE id = NEW.purchase_id;
    SELECT tenant_id, vehicle_id INTO s_company, s_vehicle
      FROM vehicles_vehiclesale WHERE id = NEW.sale_id;
    SELECT tenant_id INTO i_company FROM investment_investor WHERE id = NEW.investor_id;
    SELECT tenant_id, module_code INTO vr_company, vr_module
      FROM tenants_companymodulestate WHERE id = NEW.vehicle_module_revision_id;
    IF v_company IS DISTINCT FROM NEW.tenant_id
       OR p_company IS DISTINCT FROM NEW.tenant_id
       OR p_vehicle IS DISTINCT FROM NEW.vehicle_id
       OR s_company IS DISTINCT FROM NEW.tenant_id
       OR s_vehicle IS DISTINCT FROM NEW.vehicle_id
       OR vr_company IS DISTINCT FROM NEW.tenant_id
       OR vr_module IS DISTINCT FROM 'vehicle_management'
       OR (NEW.investor_id IS NOT NULL AND p_investor IS DISTINCT FROM NEW.investor_id)
       OR (NEW.investor_id IS NOT NULL AND i_company IS DISTINCT FROM NEW.tenant_id)
       OR (NEW.investor_id IS NULL AND NEW.investor_share_percentage IS NOT NULL)
       OR (NEW.investor_id IS NOT NULL AND NEW.investor_share_percentage IS NULL) THEN
        RAISE EXCEPTION 'Vehicle result confirmation source or Company scope is invalid'
            USING ERRCODE = '23514';
    END IF;
    IF NEW.investor_id IS NOT NULL THEN
        SELECT tenant_id, module_code INTO ir_company, ir_module
          FROM tenants_companymodulestate WHERE id = NEW.investment_module_revision_id;
        IF ir_company IS DISTINCT FROM NEW.tenant_id OR ir_module IS DISTINCT FROM 'investment' THEN
            RAISE EXCEPTION 'Vehicle result Investment revision is invalid'
                USING ERRCODE = '23514';
        END IF;
    ELSIF NEW.investment_module_revision_id IS NOT NULL THEN
        RAISE EXCEPTION 'Company-funded Vehicle result cannot carry an Investment revision'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION investment_vehicle_result_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Vehicle result confirmations are append-only'
        USING ERRCODE = '23514';
END;
$$;

CREATE FUNCTION investment_vehicle_result_audit_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM accounts_accountsecurityevent event
         WHERE event.action = 'investment.vehicle_result.confirm'
           AND event.company_id = NEW.tenant_id
           AND event.resource_id = NEW.id
           AND event.actor_id = NEW.confirmed_by_id
           AND event.reason = NEW.reason
           AND event.metadata->>'result_id' = NEW.id::text
           AND event.metadata->>'vehicle_id' = NEW.vehicle_id::text
           AND event.metadata->>'source_version' = NEW.source_version
    ) THEN
        RAISE EXCEPTION 'Vehicle result confirmation requires matching audit evidence'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;
CREATE TRIGGER investment_vehicle_result_scope
BEFORE INSERT ON investment_vehicleresultconfirmation
FOR EACH ROW EXECUTE FUNCTION investment_vehicle_result_scope_guard();
CREATE TRIGGER investment_vehicle_result_immutable
BEFORE UPDATE OR DELETE ON investment_vehicleresultconfirmation
FOR EACH ROW EXECUTE FUNCTION investment_vehicle_result_immutable();
CREATE CONSTRAINT TRIGGER investment_vehicle_result_audit
AFTER INSERT ON investment_vehicleresultconfirmation
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_vehicle_result_audit_guard();

CREATE FUNCTION investment_exit_request_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    i_company uuid;
    inv_revision_company uuid;
    inv_revision_module text;
    portal_revision_company uuid;
    portal_revision_module text;
BEGIN
    SELECT tenant_id INTO i_company FROM investment_investor WHERE id = NEW.investor_id;
    SELECT tenant_id, module_code INTO inv_revision_company, inv_revision_module
      FROM tenants_companymodulestate WHERE id = NEW.investment_module_revision_id;
    SELECT tenant_id, module_code INTO portal_revision_company, portal_revision_module
      FROM tenants_companymodulestate WHERE id = NEW.portal_module_revision_id;
    IF i_company IS DISTINCT FROM NEW.tenant_id
       OR inv_revision_company IS DISTINCT FROM NEW.tenant_id
       OR inv_revision_module IS DISTINCT FROM 'investment'
       OR portal_revision_company IS DISTINCT FROM NEW.tenant_id
       OR portal_revision_module IS DISTINCT FROM 'investor_portal' THEN
        RAISE EXCEPTION 'Investor Exit request scope or module revision is invalid'
            USING ERRCODE = '23514';
    END IF;
    IF TG_OP = 'UPDATE' THEN
        IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
           OR NEW.investor_id IS DISTINCT FROM OLD.investor_id
           OR NEW.terms_version IS DISTINCT FROM OLD.terms_version
           OR NEW.terms_accepted_at IS DISTINCT FROM OLD.terms_accepted_at
           OR NEW.requested_by_id IS DISTINCT FROM OLD.requested_by_id
           OR NEW.investment_module_revision_id IS DISTINCT FROM OLD.investment_module_revision_id
           OR NEW.portal_module_revision_id IS DISTINCT FROM OLD.portal_module_revision_id THEN
            RAISE EXCEPTION 'Investor Exit request source fields are immutable'
                USING ERRCODE = '23514';
        END IF;
        IF NOT ((OLD.status = 'REQUESTED' AND NEW.status = 'CANCELLATION_PENDING')
             OR (OLD.status = 'CANCELLATION_PENDING' AND NEW.status IN ('REQUESTED', 'CANCELLED'))) THEN
            RAISE EXCEPTION 'Investor Exit request transition is invalid'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION investment_exit_request_immutable_delete()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Investor Exit requests are retained'
        USING ERRCODE = '23514';
END;
$$;

CREATE FUNCTION investment_exit_history_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    r_company uuid;
BEGIN
    SELECT tenant_id INTO r_company FROM investment_investorexitrequest WHERE id = NEW.exit_request_id;
    IF r_company IS DISTINCT FROM NEW.tenant_id THEN
        RAISE EXCEPTION 'Investor Exit history must belong to the request Company'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION investment_exit_history_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Investor Exit request history is append-only'
        USING ERRCODE = '23514';
END;
$$;

CREATE FUNCTION investment_exit_request_history_complete()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    request_id uuid;
    request_status text;
    request_company uuid;
    latest_status text;
    latest_company uuid;
BEGIN
    request_id := NEW.id;
    IF TG_TABLE_NAME = 'investment_investorexitrequesthistory' THEN
        request_id := NEW.exit_request_id;
    END IF;
    SELECT tenant_id, status INTO request_company, request_status
      FROM investment_investorexitrequest WHERE id = request_id;
    SELECT tenant_id, new_status INTO latest_company, latest_status
      FROM investment_investorexitrequesthistory
     WHERE exit_request_id = request_id ORDER BY version DESC, id DESC LIMIT 1;
    IF request_company IS NULL OR latest_company IS DISTINCT FROM request_company
       OR latest_status IS DISTINCT FROM request_status THEN
        RAISE EXCEPTION 'Investor Exit state requires matching immutable history'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

CREATE FUNCTION investment_exit_history_audit_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    expected_action text;
    expected_status text;
BEGIN
    expected_action := CASE NEW.action
        WHEN 'SUBMITTED' THEN 'investor.portal.exit.request'
        WHEN 'CANCELLATION_REQUESTED' THEN 'investor.portal.exit.cancel_request'
        WHEN 'CANCELLATION_APPROVED' THEN 'investor.portal.exit.cancel_review'
        WHEN 'CANCELLATION_REJECTED' THEN 'investor.portal.exit.cancel_review'
        ELSE NULL END;
    IF expected_action IS NULL OR NOT EXISTS (
        SELECT 1 FROM accounts_accountsecurityevent event
         WHERE event.action = expected_action
           AND event.company_id = NEW.tenant_id
           AND event.resource_id = NEW.exit_request_id
           AND event.actor_id = NEW.actor_id
           AND event.reason = NEW.reason
           AND event.metadata->>'exit_request_id' = NEW.exit_request_id::text
           AND event.metadata->>'status' = NEW.new_status
    ) THEN
        RAISE EXCEPTION 'Investor Exit transition requires matching audit evidence'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

CREATE TRIGGER investment_exit_request_insert_update_guard
BEFORE INSERT OR UPDATE ON investment_investorexitrequest
FOR EACH ROW EXECUTE FUNCTION investment_exit_request_guard();
CREATE TRIGGER investment_exit_request_delete_guard
BEFORE DELETE ON investment_investorexitrequest
FOR EACH ROW EXECUTE FUNCTION investment_exit_request_immutable_delete();
CREATE TRIGGER investment_exit_history_scope
BEFORE INSERT ON investment_investorexitrequesthistory
FOR EACH ROW EXECUTE FUNCTION investment_exit_history_guard();
CREATE TRIGGER investment_exit_history_immutable_guard
BEFORE UPDATE OR DELETE ON investment_investorexitrequesthistory
FOR EACH ROW EXECUTE FUNCTION investment_exit_history_immutable();
CREATE CONSTRAINT TRIGGER investment_exit_request_history_complete
AFTER INSERT OR UPDATE ON investment_investorexitrequest
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_exit_request_history_complete();
CREATE CONSTRAINT TRIGGER investment_exit_history_state_complete
AFTER INSERT ON investment_investorexitrequesthistory
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_exit_request_history_complete();
CREATE CONSTRAINT TRIGGER investment_exit_history_audit
AFTER INSERT ON investment_investorexitrequesthistory
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_exit_history_audit_guard();
"""

REVERSE_SQL = r"""
DROP TRIGGER investment_exit_history_audit ON investment_investorexitrequesthistory;
DROP TRIGGER investment_exit_history_state_complete ON investment_investorexitrequesthistory;
DROP TRIGGER investment_exit_request_history_complete ON investment_investorexitrequest;
DROP TRIGGER investment_exit_history_immutable_guard ON investment_investorexitrequesthistory;
DROP TRIGGER investment_exit_history_scope ON investment_investorexitrequesthistory;
DROP TRIGGER investment_exit_request_delete_guard ON investment_investorexitrequest;
DROP TRIGGER investment_exit_request_insert_update_guard ON investment_investorexitrequest;
DROP FUNCTION investment_exit_history_audit_guard();
DROP FUNCTION investment_exit_request_history_complete();
DROP FUNCTION investment_exit_history_immutable();
DROP FUNCTION investment_exit_history_guard();
DROP FUNCTION investment_exit_request_immutable_delete();
DROP FUNCTION investment_exit_request_guard();
DROP TRIGGER investment_vehicle_result_audit ON investment_vehicleresultconfirmation;
DROP TRIGGER investment_vehicle_result_immutable ON investment_vehicleresultconfirmation;
DROP TRIGGER investment_vehicle_result_scope ON investment_vehicleresultconfirmation;
DROP FUNCTION investment_vehicle_result_audit_guard();
DROP FUNCTION investment_vehicle_result_immutable();
DROP FUNCTION investment_vehicle_result_scope_guard();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("investment", "0011_investorexitrequest_investorexitrequesthistory_and_more"),
        ("vehicles", "0010_vehiclepurchase_investor_share_agreement_and_more"),
        ("accounts", "0012_scope_end_monotonic"),
        ("tenants", "0003_company_module_state"),
    ]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
