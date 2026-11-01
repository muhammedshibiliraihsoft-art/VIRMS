"""Small process targets used to verify shared PostgreSQL login admission."""


def admit_login_in_process(login_id, remote_addr, database_name, barrier, result_queue):
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    import django

    django.setup()

    from django.db import connections
    from django.test import RequestFactory

    from apps.accounts.login_admission import login_attempt

    connections["default"].close()
    connections["default"].settings_dict["NAME"] = database_name
    request = RequestFactory().post("/api/v1/auth/login/")
    request.META["REMOTE_ADDR"] = remote_addr
    barrier.wait(timeout=30)
    with login_attempt(request, login_id) as outcome:
        result = (outcome.allowed, outcome.retry_after)
        if outcome.allowed:
            outcome.authenticated = False
    result_queue.put(result)
    connections.close_all()
