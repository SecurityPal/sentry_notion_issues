# Sentry-Notion Integration

This integration allows us to create and link tasks to the notion Engineering Task List database, from Sentry.

## Configuration

### Environment Variables

The integration requires the following environment variables to be set, which can all be found in GCP secret manager.

- `NOTION_TOKEN`: The notion API integration token.
- `NOTION_CONFIG`: JSON configuration for the Notion database (see below)
- `SENTRY_NOTION_INTEGRATION_CLIENT_SECRET`: The client secret for validating Sentry requests.

### Ngrok

The integration requires a ngrok tunnel to be set up in order to receive requests from Sentry. You can run `make ngrok-up` to set up the tunnel and within the Sentry app, you need to modify the webhook URL to use the ngrok URL if you want to test the integration.

### Notion Configuration

The `NOTION_CONFIG` environment variable should contain a JSON object with the following structure:

```json
{
  "database_id": "your-notion-database-id",
  "columns": {
    "assignee_id": "notion-people-property-id",
    "issue_id": "notion-unique-id-property-id",
    "sentry_url_id": "notion-url-property-id"
  }
}
```

We use the `NOTION_CONFIG` to map between the Notion database columns and the properties we want to use in the integration. We use ids so that we can avoid issues with property names changing.

## Authentication

All requests from Sentry are authenticated using HMAC signature validation. The integration verifies that requests are coming from Sentry by checking the `sentry-hook-signature` or `sentry-app-signature` headers against the client secret.

## Caching

The integration uses Redis to cache Notion database metadata and user information to improve performance and reduce API calls to Notion. The cache timeout is set to 6 hours by default.

## Sentry UI Integration

The `sentry_ui_schema.json` file defines the UI components that appear in the Sentry interface, allowing users to. Changes to this file need to be copy pasted into the Sentry UI schema editor within the Sentry app.
