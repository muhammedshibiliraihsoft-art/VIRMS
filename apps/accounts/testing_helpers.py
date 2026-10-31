"""Small process targets used to verify shared PostgreSQL login admission."""


def admit_login_in_process(login_id, remote_addr, database_name, barrier, result_queue):
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    import django

    django.setup()

    from django.db import connections
    from django.test import RequestFactory

    from apps.accounts.login_admission import admit_login

    connections["default"].close()
    connections["default"].settings_dict["NAME"] = database_name
    request = RequestFactory().post("/api/v1/auth/login/")
    request.META["REMOTE_ADDR"] = remote_addr
    barrier.wait(timeout=30)
    result_queue.put(admit_login(request, login_id))
    connections.close_all()
