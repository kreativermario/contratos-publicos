# Security

## Reporting a vulnerability

Use GitHub's private vulnerability reporting on this repository
(Security -> Report a vulnerability). It is private by default and does not
require an email address from either of us.

Please do not open a public issue for a security problem.

There is no bounty. This is an unfunded civic project.

### In scope

* The deployed site and its API.
* This repository: the application code, the container definitions, the nginx
  configuration, the deploy workflow.
* Anything that would let someone read or write data they should not, run code
  on the host, or take the service down cheaply.

### Out of scope

* **The upstream data.** Wrong, missing or duplicated contracts come from the
  public register, not from us. See "Data corrections" below.
* Missing security headers with no demonstrated impact, and findings copied
  straight out of an automated scanner with no working proof.
* Denial of service by volume. The site is rate limited and sits behind a CDN;
  please do not test that by doing it.
* Social engineering, physical access, and anything touching a third party's
  systems.

## Data corrections

**A wrong number is not a security issue, and usually it is not our bug.**

This project reads the public contract register and shows what is in it. It
does not correct it. If a contract is wrong, missing, or attributed to the
wrong entity, the fix has to happen at the source, with IMPIC, through
dados.gov.pt or the Portal BASE. Once it is fixed there it will appear here on
the next ingest.

If you think we have read the register correctly but calculated something
wrongly, that is a real bug and we want it: open a normal issue and include the
contract id or the NIF so it can be reproduced.

## What this project is not

Nothing here is an accusation. Ajuste direto is a legal procedure. The
indicators measure what is observable in the public record and the interface
says so. If you are named on this site and believe the underlying record is
wrong, the correction route above is the one that will actually work.
