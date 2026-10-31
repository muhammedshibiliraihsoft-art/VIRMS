from rest_framework.authentication import SessionAuthentication


class BrowserSessionAuthentication(SessionAuthentication):
    def authenticate_header(self, request):
        return "Session"
