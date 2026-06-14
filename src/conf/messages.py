"""Application messages module.

This module defines constant string messages used throughout the application
for user feedback, error details, and system responses.
These messages help maintain consistency and centralize text content.
"""

USER_EMAIL_OR_NAME_ALREADY_EXISTS = "User with email or name already exists"
UNVERIFIED_CREDENTIALS = "Could not verify credentials"
INVALID_CREDENTIALS = "Wrong email or password"
INTEGRITY_ERROR = "Data integrity error"
INVALID_REFRESH_TOKEN = "Invalid or expired refresh token"
EXCEED_REQUESTS_LIMIT = "Too many requests"
USER_NOT_CONFIRMED = "Email address is not confirmed"
USER_NOT_FOUND = "User not found"
USER_ALREADY_CONFIRMED = "Your email is already confirmed"
USER_CONFIRMED = "Your email is confirmed"
UNEXISTING_TOKEN = "Unexisting token for mail confirmation"
EMAIL_SENT = "Email with confirmation sent"
REQUEST_LIMIT_EXCEEDED = "Request limit exceeded. Please try again later."
FAILED_CONNECT_TO_DB = "Error connecting to the database"
BAD_CONFIG_DB = "Database is not configured correctly"
SUCCESSFUL_HEALTHCHECK = "Welcome to FastAPI!"
DB_SESSION_IS_NOT_INIT = "Database session is not initialized"
