from google.auth import impersonated_credentials, default, transport
import logging

def render_impersonation_chain(user, project_id):
    return f'{user}@{project_id}.iam.gserviceaccount.com'


class ServiceAccountImpersonationCredentialManager:
    target_scopes = ['https://www.googleapis.com/auth/cloud-platform']

    def __init__(self, target_principal):
        self._target_principal = target_principal

    def get_target_credentials(self):
        logging.debug(f'Impersonating as: {self._target_principal}')
        source_credentials, _ = default()

        target_credentials = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=self._target_principal,
            target_scopes=self.target_scopes,
            delegates=[],
            lifetime=500
        )
        return target_credentials
