from django.core.management.base import BaseCommand
from apps.project.models import Token, Contribute, Validate


class Command(BaseCommand):

    def handle(self, *args, **options):
        tokens = Token.objects.all()
        for token in tokens:
            if token.short_report and token.price_init > 0:
                token.price_ath = token.short_report.get("ath")
                token.price_atl = token.short_report.get("atl")
                token.short_report["pac"] = round(token.short_report["ath"] / token.price_init)
                token.short_report["pcc"] = round(token.price_current / token.price_init)
                token.save()
            project = token.main_projects.first()
            if project:
                init_validate = Validate.objects.filter(
                    contribute__field="INIT",
                    contribute__target_object_id=project.pk,
                    contribute__target_content_type__model="project",
                    contribute__target_content_type__app_label="project",
                    wallet=project.wallet
                ).first()
                if init_validate:
                    project.score_hunt = init_validate.power
                    project.save()

