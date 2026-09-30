# Security Notes

- Treat uploaded documents as sensitive engineering data.
- Do not commit proprietary PDFs, source code, credentials or `.env` files.
- The pilot is single-user and does not implement enterprise RBAC/IAM.
- LLM prompts explicitly treat retrieved repository/document text as untrusted content.
- For production, add authentication, authorization, project isolation, encryption, secret management, network controls, retention policies and centralized audit logging.
- Generated architecture findings are advisory and require qualified human review before design approval, release or vehicle validation.
