from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def live(request):
    return JsonResponse({"status": "live"})


@require_GET
def ready(request):
    try:
        from django.db.migrations.executor import MigrationExecutor

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        executor = MigrationExecutor(connection)
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if pending:
            return JsonResponse({"status": "unready"}, status=503)
    except Exception:
        return JsonResponse({"status": "unready"}, status=503)
    return JsonResponse({"status": "ready"})
