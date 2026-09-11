# Production Incident and Rollback Runbook

1. Confirm the customer impact and record the incident start time.
2. Pause further production deployments.
3. Identify the last known-good tagged release.
4. Check whether database changes are backward compatible before rollback.
5. Redeploy the known-good release.
6. Verify homepage, signup, login, primary workflow, support and return-login journeys.
7. Communicate material customer impact truthfully when required.
8. Investigate the failed change away from production pressure.
9. Add a regression test, complete human review and release through preview.
10. Record cause, impact, recovery time, evidence and prevention actions.

Git rollback does not restore deleted database records, customer uploads, external services or secrets. Maintain separate tested backups for those assets.
