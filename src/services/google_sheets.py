import os

from google.auth.exceptions import GoogleAuthError
from google.auth.external_account_authorized_user import (
    Credentials as FlowCredentials,
)
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.config import settings
from core.logger import get_logger
from schemas.parse_schemas import SolscanResult

logger = get_logger(__name__)


class GoogleSheets:
    def __init__(self):
        self.token_path = "token.json"
        self.credentials_path = "credentials.json"

        self.scopes = settings.sheet_scopes
        self.title = settings.sheet_title
        self.range = settings.sheet_range
        self.list = settings.sheet_first_list_name
        self.headers = settings.sheet_headers
        self.creds = self.initialize_credentials()

    def initialize_credentials(self) -> Credentials | FlowCredentials:
        logger.info("Initializing Google Sheets credentials.")

        creds = None
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(
                    self.token_path, self.scopes
                )
                logger.info("Loaded credentials from token file.")
            except Exception as e:
                logger.error(
                    f"Failed to load credentials from token file: {e}"
                )
        if not creds or not creds.valid:
            creds = self.refresh_credentials(creds)

        return creds

    def refresh_credentials(
        self, creds: Credentials | FlowCredentials | None
    ) -> Credentials | FlowCredentials:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Credentials refreshed successfully.")
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                creds = self.run_authentication_flow()
        else:
            creds = self.run_authentication_flow()
        self.save_credentials(creds)
        return creds

    def run_authentication_flow(self) -> Credentials | FlowCredentials:
        logger.info("Running authentication flow.")
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.scopes
            )
            creds = flow.run_local_server(port=0)
            logger.info("Authentication flow completed.")
        except Exception as e:
            logger.error(f"Authentication flow failed: {e}")
            raise e
        return creds

    def save_credentials(self, creds: Credentials | FlowCredentials):
        logger.info("Saving credentials to file.")
        try:
            with open(self.token_path, "w") as token_file:
                token_file.write(creds.to_json())
                logger.info("Credentials saved successfully.")
        except IOError as e:
            logger.error(f"Unable to save credentials: {e}")

    def manage_spreadsheet(self, data: SolscanResult) -> bool:
        try:
            drive_service = build("drive", "v3", credentials=self.creds)
            sheet_service = build("sheets", "v4", credentials=self.creds)
            spreadsheet_id = self.find_or_create_spreadsheet(
                drive_service, sheet_service
            )
            if spreadsheet_id:
                logger.info(f"Try to add data: {data}")
                self.update_sheet(sheet_service, spreadsheet_id, data)
                return True
        except (HttpError, GoogleAuthError) as err:
            logger.error(f"Error managing spreadsheet: {err}")
        return False

    def find_or_create_spreadsheet(self, drive_service, sheet_service) -> str:
        logger.debug("Finding or creating spreadsheet.")
        try:
            response = (
                drive_service.files()
                .list(
                    q=f"name='{self.title}' and mimeType='application/vnd.google-apps.spreadsheet'",
                    spaces="drive",
                    fields="files(id, name)",
                )
                .execute()
            )
            files = response.get("files", [])
            if files:
                logger.info("Spreadsheet found.")
                return files[0].get("id")
            else:
                logger.info("Spreadsheet not found, creating a new one.")
                return self.create_spreadsheet(sheet_service)
        except Exception as e:
            logger.error(f"Error finding or creating spreadsheet: {e}")
            raise e

    def create_spreadsheet(self, sheet_service) -> str:
        logger.info("Creating a new spreadsheet.")
        try:
            spreadsheet = (
                sheet_service.spreadsheets()
                .create(body={"properties": {"title": self.title}})
                .execute()
            )
            spreadsheet_id = spreadsheet.get("spreadsheetId")
            self.setup_sheet(sheet_service, spreadsheet_id)
            logger.info("New spreadsheet created.")
            return spreadsheet_id
        except Exception as e:
            logger.error(f"Error creating spreadsheet: {e}")
            raise e

    def setup_sheet(
        self,
        sheet_service,
        spreadsheet_id: str,
    ):
        logger.info("Setting up the spreadsheet.")
        try:
            sheet_id = (
                sheet_service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id)
                .execute()["sheets"][0]["properties"]["sheetId"]
            )
            batch_update_spreadsheet_request_body = {
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": sheet_id,
                                "title": self.list,
                            },
                            "fields": "title",
                        }
                    }
                ]
            }
            sheet_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=batch_update_spreadsheet_request_body,
            ).execute()
            sheet_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{self.list}!A1",
                body={"values": [self.headers]},
                valueInputOption="USER_ENTERED",
            ).execute()
            logger.info("Spreadsheet setup completed.")
        except Exception as e:
            logger.error(f"Error setting up spreadsheet: {e}")
            raise e

    def update_sheet(
        self,
        sheet_service,
        spreadsheet_id: str,
        data: SolscanResult,
    ):
        logger.debug("Updating the spreadsheet with new data.")
        try:
            values = [
                [
                    str(data.date),
                    data.hash,
                    data.sol_count,
                    data.sol_usd,
                    data.spl_count,
                    data.spl_usd,
                ],
            ]
            body = {"values": values}
            sheet_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=self.range,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()
            logger.debug("Data appended to the spreadsheet successfully.")
        except Exception as e:
            logger.error(f"Error updating the spreadsheet: {e}")
            raise e
