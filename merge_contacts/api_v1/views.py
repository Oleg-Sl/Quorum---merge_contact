from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework import views, viewsets, filters, status
from rest_framework.response import Response


from .service import handler, bx24_tokens


# Обработчик установки приложения
class InstallAppApiView(views.APIView):
    @xframe_options_exempt
    def post(self, request):
        data = {
            "domain": request.query_params.get("DOMAIN", ""),
            "auth_token": request.data.get("AUTH_ID", ""),
            "expires_in": request.data.get("AUTH_EXPIRES", 3600),
            "refresh_token": request.data.get("REFRESH_ID", ""),
            "application_token": request.query_params.get("APP_SID", ""),
            'client_endpoint': f'https://{request.query_params.get("DOMAIN", "")}/rest/',
        }
        bx24_tokens.create_secrets_bx24(data)
        return render(request, 'install.html')


# Обработчик удаления приложения
class UninstallAppApiView(views.APIView):
    @xframe_options_exempt
    def post(self, request):
        return Response(status.HTTP_200_OK)


# Обработчик установленного приложения
class IndexApiView(views.APIView):
    @xframe_options_exempt
    def post(self, request):
        return render(request, 'index.html')

    @xframe_options_exempt
    def get(self, request):
        return render(request, 'index.html')


class DealCreateUpdateViewSet(views.APIView):
    """ Контроллер обработки событий BX24: onVoximplantCallEnd """
    def post(self, request):
        event = request.data.get("event", "")
        id_deal = request.data.get("data[FIELDS][ID]", None)
        application_token = request.data.get("auth[application_token]", None)

        # if not verification_app.verification(application_token):
        #     return Response("Unverified event source", status=status.HTTP_400_BAD_REQUEST)

        if not id_deal:
            return Response("Not transferred ID deal", status=status.HTTP_400_BAD_REQUEST)

        status_code, msg = handler.add_company_in_deal(id_deal)

        if status_code == 200:
            return Response(msg, status=status.HTTP_200_OK)
        else:
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
