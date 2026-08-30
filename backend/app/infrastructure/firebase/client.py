"""Firebase Admin SDK initialization.

This is the ONLY module allowed to construct the Firebase Admin App (see
docs/01-CLAUDE.md rule 6 and docs/07-CODE_STANDARDS.md #15). Repository
implementations (added in a later phase) obtain Firestore/Auth clients
through get_firestore_client() / get_auth_client() rather than importing
firebase_admin directly.
"""

import os
from functools import lru_cache
from types import ModuleType

import firebase_admin
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from firebase_admin import auth, credentials, firestore
from google.cloud.firestore import Client as FirestoreClient

from app.core.config import Settings, get_settings


def _emulator_credential() -> credentials.Base:
    """`credentials.ApplicationDefault()` still requires discoverable
    Application Default Credentials even when every read/write is actually
    going to a local emulator — confirmed against a real, running
    `firebase emulators:start` in Phase 10 (this whole module was, until
    then, "NOT runtime-verified" per every repository file's docstring):
    it raised `DefaultCredentialsError` before ever reaching the emulator,
    contradicting this module's own prior claim that "no service account
    file [is] needed" for emulator mode (the Node.js Admin SDK doesn't
    have this requirement; the Python one does — a documented, known
    limitation, not something specific to this project).

    Since the emulator never validates the credential it's given, a
    throwaway, locally-generated RSA keypair — built in-memory, never
    written to disk, never touching a real Google service — is sufficient
    and lets `firebase emulators:start` work out of the box for any
    developer, with no manual `GOOGLE_APPLICATION_CREDENTIALS` workaround."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    return credentials.Certificate(
        {
            "type": "service_account",
            "project_id": "emulator",
            "private_key_id": "emulator",
            "private_key": private_key_pem,
            "client_email": "emulator@emulator.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )


def _build_app(settings: Settings) -> firebase_admin.App:
    using_emulator = False
    if settings.firestore_emulator_host:
        os.environ["FIRESTORE_EMULATOR_HOST"] = settings.firestore_emulator_host
        using_emulator = True
    if settings.firebase_auth_emulator_host:
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = settings.firebase_auth_emulator_host
        using_emulator = True

    if settings.firebase_service_account_path:
        cred = credentials.Certificate(settings.firebase_service_account_path)
    elif using_emulator:
        cred = _emulator_credential()
    else:
        cred = credentials.ApplicationDefault()

    return firebase_admin.initialize_app(cred, options={"projectId": settings.firebase_project_id})


@lru_cache
def get_firebase_app() -> firebase_admin.App:
    return _build_app(get_settings())


@lru_cache
def get_firestore_client() -> FirestoreClient:
    return firestore.client(app=get_firebase_app())


def get_auth_client() -> ModuleType:
    return auth
