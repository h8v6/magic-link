# Project Roadmap

This document outlines the future direction and planned evolution of the `magic-link` library. Our goal is to manage expectations and provide transparency for our users and contributors.

### Version 1.1 - Ecosystem Expansion

**Theme:** Broadening provider support without altering the core API.

*   **AWS SES Mailer Backend:** A new `SESMailer` that implements the `MailerInterface`. It will use `boto3` for authentication and will be installable via the `ses` extra.
*   **SendGrid Mailer Backend:** A new `SendGridMailer` using SendGrid's official Python library, installable via the `sendgrid` extra.
*   **Rationale:** Natively supporting the most popular email delivery services significantly lowers the barrier to entry for a large number of developers.

### Version 1.2 - Performance & Advanced Configuration

**Theme:** Optimizing for high-traffic scenarios and providing more granular control.

*   **Async Database Drivers:** The `SQLAlchemyStorage` backend will be enhanced to support async drivers like `asyncpg` for PostgreSQL, improving I/O performance.
*   **Granular Token Configuration:** We will expose options to configure token TTL, length, and character sets directly via the `MagicLinkConfig` object.
*   **Rationale:** As projects scale, they encounter performance bottlenecks and unique security requirements. This release will address those advanced use cases.

### Future / v2.0 - Strategic Evolution

**Theme:** Introducing powerful new capabilities that may require opt-in breaking changes.

*   **Optional User Management:** A potential built-in layer to handle user creation on their first magic link login and store basic metadata, enabled by a configuration flag.
*   **Alternative Token Types:** Potential support for different token styles, such as short, numeric OTPs suitable for SMS delivery.
*   **Rationale:** These features would address common adjacent problems in authentication, evolving the library from a specialized tool into a more comprehensive solution. Any work in this area will be preceded by a detailed public design discussion.
