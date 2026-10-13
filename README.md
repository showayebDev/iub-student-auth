# IRAS student authentication client

This folder contains reusable Python and JavaScript functions for an
authorized student application:

> Note: Some information in `frontend-auth-analysis-prompt.txt` is inaccurate.

- `student_auth.py` — Python implementation
- `studentAuth.js` — Node.js implementation using the built-in `crypto` and
  `fetch` APIs
- `student_auth.go` — Go implementation using the standard library

Do not commit student IDs, passwords, access tokens, or API responses. Store
credentials in a secure secret manager or collect them at runtime. Treat
access tokens as secrets and never log them.

## Algorithm

The public IRAS frontend transforms the plaintext password before sending the
login request:

1. Encode the password as UTF-8.
2. Encrypt it with AES-128 in CBC mode.
3. Use PKCS#7 padding to fill the 16-byte AES block size.
4. Use the following frontend-embedded values as UTF-8 bytes:

   ```text
   Key: rW7aT6RZoP3hjtz0
   IV:  V3k6oMP7C8Jt3E4z
   ```

5. Encode the ciphertext as standard Base64.
6. Send JSON to:

   ```text
   POST https://iras.iub.edu.bd:8079/v3/account/token
   ```

   with this shape:

   ```json
   {
     "email": "<student ID>",
     "password": "<Base64 ciphertext>"
   }
   ```

The request uses JSON content headers plus the frontend origin and referrer.
On success, the access token is returned in `data[0].access_token`. Some
responses may provide `access_token` at the top level, so both shapes are
handled. Both functions return this object:

```json
{
  "access_token": "<server-issued token>",
  "expires": "<server expiry timestamp or null>"
}
```

The `expires` value is read directly from the server response. It may be
`null` if the server does not provide an expiry timestamp.

## Python

Install the dependency in the project environment:

```powershell
uv pip install cryptography
```

Use the function:

```python
from student_auth import get_token

auth = get_token(student_id, password)
token = auth["access_token"]
expires = auth["expires"]
```

`token` is the bearer token and `expires` is the server-provided expiry
timestamp.

## JavaScript

Node.js 18 or newer is recommended because it provides `fetch`:

```javascript
const { getToken } = require("./studentAuth");

async function authenticate(studentId, password) {
  const { access_token, expires } = await getToken(studentId, password);
  // Keep both values in memory; do not log them.
  return { access_token, expires };
}
```

`GetToken` returns an `AuthResult` with `AccessToken` and a nullable
`Expires` timestamp. The Go client uses only the standard library.

## Security limitations

The AES key and IV are present in the public frontend bundle, so this
transformation is obfuscation rather than a secret cryptographic protocol.
HTTPS protects the request in transit. A production student app should also
use secure token storage, short token lifetimes where supported, logout and
token revocation, server-side authorization checks, and no token values in
logs, URLs, analytics, or crash reports.
