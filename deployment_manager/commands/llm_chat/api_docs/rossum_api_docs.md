

# Getting Started


## Introduction

The Rossum API allows you to programmatically access and manage your
organization's Rossum data and account information. The API allows you to do the
following programmatically:
- Manage yourorganization,users,workspacesandqueues
- Configure captured data: selectextracted fields
- Integrate Rossum with other systems:import,export,extensions
On this page, you will find an introduction to the API usage from a developer
perspective, and a reference to all the API objects and methods.


## Developer Resources

There are several other key resources related to implementing, integrating
and extending the Rossum platform:
- Refer to theRossum Developer Portalfor guides, tutorials, news and a community Q&A section.
- Subscribe to therossum-api-announcementsgroup to stay up to date on the API and platform updates.
- For managing and configuring your account, use therossumcommand-line tool.(Setup instructions.)
- For a management overview of Rossum implementation options, see theRossum Integration Whitepaper.
- If you are an RPA developer, refer to ourUiPathorBluePrismguides.


## Quick API Tutorial

For a quick tutorial on how to authenticate, upload a document and export extracted
data, see the sections below. If you want to skip this quick tutorial, continue directly
to theOverview section.
It is a good idea to go through theintroduction to the Rossum platformon the Developer Portal first to make sure you are up to speed on the basic Rossum concepts.
If in trouble, feel free to contact us atsupport@rossum.ai.

#### Install curl tool

Test curl is installed properly

```
curl https://<example>.rossum.app/api/v1
```

curl https://<example>.rossum.app/api/v1

```
{"organizations":"https://<example>.rossum.app/api/v1/organizations","workspaces":"https://<example>.rossum.app/api/v1/workspaces","schemas":"https://<example>.rossum.app/api/v1/schemas","connectors":"https://<example>.rossum.app/api/v1/connectors","inboxes":"https://<example>.rossum.app/api/v1/inboxes","queues":"https://<example>.rossum.app/api/v1/queues","documents":"https://<example>.rossum.app/api/v1/documents","users":"https://<example>.rossum.app/api/v1/users","groups":"https://<example>.rossum.app/api/v1/groups","annotations":"https://<example>.rossum.app/api/v1/annotations","pages":"https://<example>.rossum.app/api/v1/pages"}
```

{"organizations":"https://<example>.rossum.app/api/v1/organizations","workspaces":"https://<example>.rossum.app/api/v1/workspaces","schemas":"https://<example>.rossum.app/api/v1/schemas","connectors":"https://<example>.rossum.app/api/v1/connectors","inboxes":"https://<example>.rossum.app/api/v1/inboxes","queues":"https://<example>.rossum.app/api/v1/queues","documents":"https://<example>.rossum.app/api/v1/documents","users":"https://<example>.rossum.app/api/v1/users","groups":"https://<example>.rossum.app/api/v1/groups","annotations":"https://<example>.rossum.app/api/v1/annotations","pages":"https://<example>.rossum.app/api/v1/pages"}
All code samples included in this API documentation usecurl, the command
line data transfer tool. On MS Windows 10, MacOS X and most Linux
distributions, curl should already be pre-installed. If not, please download
it fromcurl.haxx.se).
curl
Optionally usejqtool to pretty-print JSON output
jq

```
curl https://<example>.rossum.app/api/v1 | jq
```

curl https://<example>.rossum.app/api/v1 | jq

```
{"organizations":"https://<example>.rossum.app/api/v1/organizations","workspaces":"https://<example>.rossum.app/api/v1/workspaces","schemas":"https://<example>.rossum.app/api/v1/schemas","connectors":"https://<example>.rossum.app/api/v1/connectors","inboxes":"https://<example>.rossum.app/api/v1/inboxes","queues":"https://<example>.rossum.app/api/v1/queues","documents":"https://<example>.rossum.app/api/v1/documents","users":"https://<example>.rossum.app/api/v1/users","groups":"https://<example>.rossum.app/api/v1/groups","annotations":"https://<example>.rossum.app/api/v1/annotations","pages":"https://<example>.rossum.app/api/v1/pages"}
```

{"organizations":"https://<example>.rossum.app/api/v1/organizations","workspaces":"https://<example>.rossum.app/api/v1/workspaces","schemas":"https://<example>.rossum.app/api/v1/schemas","connectors":"https://<example>.rossum.app/api/v1/connectors","inboxes":"https://<example>.rossum.app/api/v1/inboxes","queues":"https://<example>.rossum.app/api/v1/queues","documents":"https://<example>.rossum.app/api/v1/documents","users":"https://<example>.rossum.app/api/v1/users","groups":"https://<example>.rossum.app/api/v1/groups","annotations":"https://<example>.rossum.app/api/v1/annotations","pages":"https://<example>.rossum.app/api/v1/pages"}
You may also want to installjqtool to make curl output human-readable.
jq

#### Use the API on Windows

This API documentation is written for usage in command line interpreters running on UNIX based operation systems (Linux and Mac).
Windows users may need to use the following substitutions when working with API:
Character used in this documentationMeaning/usageSubstitute character for Windows users'single quotes""double quotes"" or \"\continue the command on the next line^
Example of API call on UNIX-based OS

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"target_queue": "https://<example>.rossum.app/api/v1/queues/8236", "target_status": "to_review"}'\'https://<example>.rossum.app/api/v1/annotations/315777/copy'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"target_queue": "https://<example>.rossum.app/api/v1/queues/8236", "target_status": "to_review"}'\'https://<example>.rossum.app/api/v1/annotations/315777/copy'
Examples of API call on Windows

```
curl-H"Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03"-H"Content-Type: application/json"^-d"{""target_queue"": ""https://<example>.rossum.app/api/v1/queues/8236"", ""target_status"": ""to_review""}"^"https://<example>.rossum.app/api/v1/annotations/315777/copy"curl-H"Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03"-H"Content-Type: application/json"^-d"{\"target_queue\":\"https://<example>.rossum.app/api/v1/queues/8236\",\"target_status\":\"to_review\"}"^"https://<example>.rossum.app/api/v1/annotations/315777/copy"
```

curl-H"Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03"-H"Content-Type: application/json"^-d"{""target_queue"": ""https://<example>.rossum.app/api/v1/queues/8236"", ""target_status"": ""to_review""}"^"https://<example>.rossum.app/api/v1/annotations/315777/copy"curl-H"Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03"-H"Content-Type: application/json"^-d"{\"target_queue\":\"https://<example>.rossum.app/api/v1/queues/8236\",\"target_status\":\"to_review\"}"^"https://<example>.rossum.app/api/v1/annotations/315777/copy"

#### Create an account

In order to interact with the API, you need an account. If you do not have one,
you can create one via ourself-service portal.

#### Login to the account

Fill-in your username and password (login credentials to work with API are the same
as those to log into your account.). Trigger login endpoint to obtain a key (token),
that can be used in subsequent calls.

```
curl -s -H 'Content-Type: application/json' \
  -d '{"username": "east-west-trading-co@example.com", "password": "aCo2ohghBo8Oghai"}' \
  'https://<example>.rossum.app/api/v1/auth/login'
{"key": "db313f24f5738c8e04635e036ec8a45cdd6d6b03"}
```

This key will be valid for a default expire time (currently 162 hours) or until you log out from the sessions.
curl

#### Upload a document

In order to upload a document (PDF, image, XLSX, XLS, DOCX, DOC) through the API, you need to obtain the id of aqueuefirst.

```
curl -s -H 'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
  'https://<example>.rossum.app/api/v1/queues?page_size=1' | jq -r .results[0].url
https://<example>.rossum.app/api/v1/queues/8199
```

Then you can upload document to the queue. Alternatively, you can send
documents to a queue-related inbox. Seeuploadfor more information
about importing files.

```
curl -s -H 'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03' \
  -F content=@document.pdf 'https://<example>.rossum.app/api/v1/uploads?queue=8199' | jq -r .url
https://<example>.rossum.app/api/v1/tasks/9231
```


#### Wait for document to be ready and review extracted data

As soon as a document is uploaded, it will show up in the queue and the data extraction will begin.
It may take a few seconds to several minutes to process a document. You can check status
of the annotation and wait until its status is changed toto_review.
to_review

```
curl -s -H 'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03' \
  'https://<example>.rossum.app/api/v1/annotations/319668' | jq .status
"to_review"
```

After that, you can open the Rossum web interfaceexample.rossum.appto review and confirm extracted data.

#### Download reviewed data

Now you can export extracted data using theexportendpoint of the queue. You
can select XML, CSV, XLSX or JSON format. For CSV, use URL like:
export

```
curl -s -H 'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03' \
  'https://<example>.rossum.app/api/v1/queues/8199/export?status=exported&format=csv&id=319668'
Invoice number,Invoice Date,PO Number,Due date,Vendor name,Vendor ID,Customer name,Customer ID,Total amount,
2183760194,2018-06-08,PO2231233,2018-06-08,Alza.cz a.s.,02231233,Rossum,05222322,500.00
```


#### Logout

Finally you can dispose token safely using logout endpoint:

```
curl -s -X POST -H 'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03' \
  'https://<example>.rossum.app/api/v1/auth/logout'
{"detail":"Successfully logged out."}
```


# Overview


## HTTP and REST

The Rossum API is organized aroundREST.
Our API has predictable, resource-oriented URLs, and uses HTTP response codes
to indicate API errors. We use built-in HTTP features, like HTTP authentication
and HTTP verbs, which are understood by off-the-shelf HTTP clients.

#### HTTP Verbs

Call the API using the following standard HTTP methods:
- GET to retrieve an object or multiple objects in a specific category
- POST to create an object
- PUT to modify entire object
- PATCH to modify fields of the object
- DELETE to delete an object
We support cross-origin resource sharing, allowing you to interact securely
with our API from a client-side web application. JSON is returned by API
responses, including errors (except when another format is requested, e.g.
XML).
'Content-Type:application/json'


## Base URL

Base API endpoint URL depends on the account type, deployment and location. Default URL ishttps://<example>.rossum.app/apiwhere theexampleis the domain selected during the account creation.
URLs of companies using a dedicated deployment may look likehttps://acme.rossum.app/api.
https://<example>.rossum.app/api
example
https://acme.rossum.app/api
If you are not sure about the correct URL you can navigate tohttps://app.rossum.aiand use your email address
to receive your account information via email.
https://app.rossum.ai
Please note that we previously recommended using thehttps://api.elis.rossum.aiendpoint to interact with the Rossum
API, but now it is deprecated. For new integrations use the newhttps://<example>.rossum.app/apiendpoint.
For accounts created before Nov 2022 use thehttps://elis.rossum.ai/api.
https://api.elis.rossum.ai
https://<example>.rossum.app/api
https://elis.rossum.ai/api


## Authentication

Most of the API endpoints require a user to be authenticated. To login to the Rossum
API, post an object withusernameandpasswordfields. Login returns an access key
to be used for token authentication.
username
password
Our API also provide possibility to authenticate via One-Time token which is returned after registration.
This tokens allows users to authenticate against our API, but after one call, this token will be invalidated.
This token can be exchanged for regular access token limited only by the time of validity. For the
purpose of token exchange, use the/auth/tokenendpoint.
/auth/token
Users may delete a token using the logout endpoint or automatically after a
configured time (the default expiration time is 162 hours). The default expiration time can be lowered usingmax_token_lifetime_sfield. When the token expires, 401 status is returned.
Users are expected to re-login to obtain a new token.
max_token_lifetime_s
Rossum's API also supports session authentication, where a user session is created inside cookies after login.
If enabled, the session lasts 1 day until expired by itself or until logout
While the session is valid there is no need to send the authentication token in every request, but the "unsafe" request (POST, PUT, PATCH, DELETE),
whose MIME type is different fromapplication/jsonmust includeX-CSRFTokenheader with valid CSRF token, which is returned inside Cookie while loging in.
When a session expires, 401 status is returned as with token authentication, and users are expected to re-login to start a new session.
application/json
X-CSRFToken

### Login

Login user using username and password

```
curl-H'Content-Type: application/json'\-d'{"username": "east-west-trading-co@<example>.rossum.app", "password": "aCo2ohghBo8Oghai"}'\'https://<example>.rossum.app/api/v1/auth/login'
```

curl-H'Content-Type: application/json'\-d'{"username": "east-west-trading-co@<example>.rossum.app", "password": "aCo2ohghBo8Oghai"}'\'https://<example>.rossum.app/api/v1/auth/login'

```
{"key":"db313f24f5738c8e04635e036ec8a45cdd6d6b03","domain":"acme-corp.app.rossum.ai"}
```

{"key":"db313f24f5738c8e04635e036ec8a45cdd6d6b03","domain":"acme-corp.app.rossum.ai"}
POST /v1/auth/login
POST /v1/auth/login
Use token key in requests

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/406'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/406'
Note: The Token authorization scheme is also supported for compatibility with earlier versions.

```
curl-H'Authorization: Token db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/406'
```

curl-H'Authorization: Token db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/406'
Login user expiring after 1 hour

```
curl-H'Content-Type: application/json'\-d'{"username": "east-west-trading-co@<example>.rossum.app", "password": "aCo2ohghBo8Oghai", "max_token_lifetime_s": 3600}'\'https://<example>.rossum.app/api/v1/auth/login'
```

curl-H'Content-Type: application/json'\-d'{"username": "east-west-trading-co@<example>.rossum.app", "password": "aCo2ohghBo8Oghai", "max_token_lifetime_s": 3600}'\'https://<example>.rossum.app/api/v1/auth/login'

```
{"key":"ltcg2p2w7o9vxju313f04rq7lcc4xu2bwso423b3","domain":null}
```

{"key":"ltcg2p2w7o9vxju313f04rq7lcc4xu2bwso423b3","domain":null}
AttributeTypeRequiredDescriptionusernamestringtrueUsername of the user to be logged in.passwordstringtruePassword of the user.originstringfalseFor internal use only. Using this field may affectthrottlingof your API requests.max_token_lifetime_sintegerfalseDuration (in seconds) for which the token will be valid. Default is 162 hours which is also the maximum.

#### Response

Status:200
200
Returns object with "key", which is an access token. And the user's domain.
AttributeTypeDescriptionkeystringAccess token.domainstringThe domain the token was issued for.

### Logout

Logout user

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/auth/logout'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/auth/logout'

```
{"detail":"Successfully logged out."}
```

{"detail":"Successfully logged out."}
POST /v1/auth/logout
POST /v1/auth/logout
Logout user, discard auth token.

#### Response

Status:200
200

### Token Exchange

Exchange One-Time authentication token with a longer-lived access token.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/auth/token'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/auth/token'

```
{"key":"ltcg2p2w7o9vxju313f04rq7lcc4xu2bwso423b3","domain":"<example>.rossum.app","scope":"default"}
```

{"key":"ltcg2p2w7o9vxju313f04rq7lcc4xu2bwso423b3","domain":"<example>.rossum.app","scope":"default"}
POST /v1/auth/token
POST /v1/auth/token
AttributeTypeRequiredDescriptionscopestringfalseSupported values aredefault,approval(for internal use only)max_token_lifetime_sfloatfalseDuration (in seconds) for which the token will be valid (default: lifetime of the current token or 162 hours if the current token is one-time). Can be set to a maximum of 583200 seconds (162 hours).originstringfalseFor internal use only. Using this field may affectthrottlingof your API requests.
default
approval
This endpoint enables the exchange of a one-time token for a longer lived access token.
It is able to receive either one-time tokens provided after registration, or JWT tokens if you have such a setupconfigured. The token must be provided in a theBearerauthorization header.
Bearer

### JWT authentication

Short-lived JWT tokens can be exchanged for access tokens. A typical use case, for example, is logging in your users via SSO in your own application, and displaying the Rossum app to them embedded.
To enable JWT authentication, one needs to provide Rossum with the public key that shall be used to decode the tokens.
Currently only tokens with EdDSA (signed usingEd25519andEd448curves) and RS512 signatures are allowed, and token validity should be 60 seconds maximum.
Ed25519
Ed448
The expected formats of the header and encoded payload of the JWT token are as follows:

### Decoded JWT Header Format

Example format of a decoded JWT token header (not encrypted)

```
{"alg":"EdDSA","kid":"urn:rossum.ai:organizations:100","typ":"JWT"}
```

{"alg":"EdDSA","kid":"urn:rossum.ai:organizations:100","typ":"JWT"}
Example format of a decoded JWT token payload

```
{"ver":"1.0","iss":"ACME Corporation","aud":"https://<example>.rossum.app","sub":"john.doe@rossum.ai","exp":1514764800,"email":"john.doe@rossum.ai","name":"John F. Doe","rossum_org":"100","roles":["annotator"]}
```

{"ver":"1.0","iss":"ACME Corporation","aud":"https://<example>.rossum.app","sub":"john.doe@rossum.ai","exp":1514764800,"email":"john.doe@rossum.ai","name":"John F. Doe","rossum_org":"100","roles":["annotator"]}
AttributeTypeRequiredDescriptionkidstringtrueIdentifier. Must end with:{your Rossum org ID}, e.g."urn:rossum.ai:organizations:123"typstringfalseType of the token.algstringtrueSignature algorithm to be used for decoding the token. OnlyEdDSAorRS512values are allowed.
:{your Rossum org ID}
"urn:rossum.ai:organizations:123"
EdDSA
RS512

### Decoded JWT Payload Format

AttributeTypeRequiredDescriptionverstringtrueVersion of the payload format. Available versions:1.0.issstringtrueName of the issuer of the token (e.g. company name).audstringtrueTarget domain used for API queries (e.g.https://<example>.rossum.app)substringtrueUser email that will be matched against username in Rossum.expinttrueUNIX timestamp of the JWT token expiration. Must be set to 60 seconds after current UTC time at maximum.emailstringtrueUser email.namestringtrueUser's first name and last name separated by space. Will be used for creation of new users if auto-provisioning is enabled.rossum_orgstringtrueRossum organization id.roleslist[string]falseName of theuser rolesthat will be assigned to user created by auto-provisioning. Must be a subset of the roles stated in the auto-provisioning configuration for the organization.
1.0
https://<example>.rossum.app

#### Response

Status:200
200
AttributeTypeDescriptionkeystringAccess token.domainstringThe domain the token was issued for.scopestringSupported values aredefault,approval(for internal use only)
default
approval

### Single Sign-On (SSO)

Rossum allows customers to integrate with their ownidentity provider,
such asGoogle,Azure ADor any other provider usingOAuth2 OpenID Connectprotocol (OIDC).
Rossum then acts as aservice provider.
When SSO is enabled for an organization, user is redirected to a configured identity provider login page
and only allowed to access Rossum application when successfully authenticated.
Identity provider user claim (e.g.email(default),sub,preferred_username,unique_name)
is used to match a user account in Rossum. If auto-provisioning is enabled for
the organization, user accounts in Rossum will be automatically created for users without accounts.
email
sub
preferred_username
unique_name
Required setup of the OIDC identity provider:
- Redirect URI (also known as Reply URL):https://<example>.rossum.app/api/v1/oauth/code
https://<example>.rossum.app/api/v1/oauth/code
Required information to allow OIDC setup for the Rossum service provider:
- OIDC endpoint, such ashttps://accounts.google.com. It should support openid configuration, e.g.https://accounts.google.com/.well-known/openid-configuration
- client id
- client secret
- claim that should be matched in Rossum
- Rossum organization id
If you need to setup SSO for your organization, please contactsupport@rossum.ai.


## Pagination

All object list operations are paged by default, so you may need several API
calls to obtain all objects of given type.
ParameterDefaultMaximumDescriptionpage_size20100(*)Number of results per pagepage1Page of results
(*)Maximum page size differs for some endpoints:
- 1,000 for exporting data in CSV format via POST on /annotations
- 500 for searching in annotations via annotations/search (ifsideload=contentis not included)
sideload=content


## API Throttling

To ensure optimal performance and fair usage across the platform, the API implements throttling features. If a client exceeds the allowed
number of API requests Rossum API will respond with a429status code and aRetry-Afterheader.
The header specifies the number of seconds the client should wait before retrying the request.
To avoid being throttled, ensure your usage complies with our Acceptable Use Schedule as described in theRossum Terms of Use.
429
Retry-After
When the client receives a429status code, the response headerRetry-Afterwill have the following format:
429
Retry-After
Retry-After: 10
Retry-After: 10
This example means the client should wait for 10 seconds before attempting another request.
The recommended approach for handling throttled requests is to manage429status codes gracefully and use
exponential backoff for retries, respecting theRetry-Afterheader.
429
Retry-After

### Current Throttling Limits

The current default throttling limits for Rossum API are as follows:
LimitDescription10 reqs / secondOverall API rate limit.10 reqs / minuteLimit specific for theannotations/{id}/page_data/translateendpoint.


## Filters and ordering

List queues of workspace7540, with localeen_USand order results byname.
7540
en_US
name

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues?workspace=7540&locale=en_US&ordering=name'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues?workspace=7540&locale=en_US&ordering=name'
Lists may be filtered using various attributes.
Multiple attributes are combined with&in the URL, which results in more specific response.
Please refer to the particularobject description.
Ordering of results may be enforced by theorderingparameter and one or more
keys delimited by a comma. Preceding key with a minus sign-enforces
descending order.
ordering
-


## Metadata

Example metadata in a document object

```
{"id":319768,"url":"https://<example>.rossum.app/api/v1/documents/319768","s3_name":"05feca6b90d13e389c31c8fdeb7fea26","annotations":["https://<example>.rossum.app/api/v1/annotations/319668"],"mime_type":"application/pdf","arrived_at":"2019-02-11T19:22:33.993427Z","original_file_name":"document.pdf","content":"https://<example>.rossum.app/api/v1/documents/319768/content","metadata":{"customer-id":"f205ec8a-5597-4dbb-8d66-5a53ea96cdea","source":9581,"authors":["Joe Smith","Peter Doe"]}}
```

{"id":319768,"url":"https://<example>.rossum.app/api/v1/documents/319768","s3_name":"05feca6b90d13e389c31c8fdeb7fea26","annotations":["https://<example>.rossum.app/api/v1/annotations/319668"],"mime_type":"application/pdf","arrived_at":"2019-02-11T19:22:33.993427Z","original_file_name":"document.pdf","content":"https://<example>.rossum.app/api/v1/documents/319768/content","metadata":{"customer-id":"f205ec8a-5597-4dbb-8d66-5a53ea96cdea","source":9581,"authors":["Joe Smith","Peter Doe"]}}
When working with API objects, it may be useful to attach some information to
the object (e.g. customer id to a document). You can store custom JSON object
in ametadatasection available in most objects.
metadata
List of objects with metadata support: organization, workspace, user, queue, schema,
connector, inbox, document, annotation, page, survey.
Total metadata size may be up to 4 kB per object.


## Versioning

API Version is part of the URL, e.g.https://<example>.rossum.app/api/v1/users.
https://<example>.rossum.app/api/v1/users
To allow API progress, we consideradditionof a field in a JSON object as well asadditionof a new item in an enum object to be backward-compatible operations that
may be introduced at any time. Clients are expected to deal with such changes.


## Dates

All dates fields are represented asISO 8601formatted strings, e.g.2018-06-01T21:36:42.223415Z. All returned dates are in UTC timezone.
2018-06-01T21:36:42.223415Z


## Errors

Our API uses conventional HTTP response codes to indicate the success or failure of an API request.
CodeStatusMeaning400Bad RequestInvalid input data or error from connector.401UnauthorizedThe username/password is invalid or token is invalid (e.g. expired).403ForbiddenInsufficient permission, missing authentication, invalid CSRF token and similar issues.404Not FoundEntity not found (e.g. already deleted).405Method Not AllowedYou tried to access an endpoint with an invalid method.409ConflictTrying to change annotation that was not started by the current user.413Payload Too Largefor too large payload (especially for files uploaded).429Too Many RequestsThe allowed number of requests per minute has been exceeded. Please wait before sending more requests.500Internal Server ErrorWe had a problem with the server. Try again later.503Service UnavailableWe're temporarily offline for maintenance. Please try again later.


# Import and Export

Documents may be imported into Rossum using the REST API and email gateway.
Supported file formats arePDF,PNG,JPEG,TIFF,XLSX/XLSandDOCX/DOC.
Maximum supported file size is 40 MB (this limit applies also to the uncompressed size of the files within a.ziparchive).
.zip
In order to get the best results from Rossum the documents should be in A4
format of at least 150 DPI (in case of scans/photos). Read more aboutimport recommendations.


## Importing non-standard MIME types

Support for additional MIME types may be added by handlingupload.createdwebhook event. With this setup, user is able to pre-process
uploaded files (e.g.XMLorJSONformats) into a format that Rossum understands. Those usually need to be enabled on queue level first
(by adding appropriate mimetype toaccepted_mime_typesin queue settings attributes).
List of enabled MIME types:
- application/EDI-X12
application/EDI-X12
- application/EDIFACT
application/EDIFACT
- application/json
application/json
- application/msword
application/msword
- application/pdf
application/pdf
- application/pgp-encrypted
application/pgp-encrypted
- application/vnd.ms-excel
application/vnd.ms-excel
- application/vnd.ms-outlook
application/vnd.ms-outlook
- application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- application/vnd.openxmlformats-officedocument.wordprocessingml.document
application/vnd.openxmlformats-officedocument.wordprocessingml.document
- application/xml
application/xml
- application/zip
application/zip
- image/*
image/*
- message/rfc822
message/rfc822
- text/csv
text/csv
- text/plain
text/plain
- text/xml
text/xml
If you find your document MIME types not supported please contact Rossum support team for more information.


## Upload API

You can upload a document to the queue usinguploadendpoint with one or more files to be uploaded. You can also specify additional
field values in upload endpoint, e.g. your internal document id. As soon as a document is uploaded, data extraction
is started.
Upload endpoint supports basic authentication to enable easy integration with
third-party systems.


## Import by Email

It is also possible to send documents by email using a properly configuredinboxthat is associated with aqueue. Users then only need
to know the email address to forward emails to.
For every incoming email, Rossum extracts PDF documents, images and zip files, stores them
in the queue and starts data extraction process.
The size limit for incoming emails is 50 MB (the raw email message with base64 encoded attachments).
All the files from the root of the archive are extracted. In case the root only contains one directory (and no other files)
the whole directory is extracted. The zip files and all extracted files must be allowed inaccepted_mime_types(seequeue settings) and must pass inbox filtering rules
(see document rejection conditions) in order for annotations to be created.
accepted_mime_types
Invalid characters in attachment file names (e.g./) are replaced with underscores.
/
Small images (up to 100x100 pixels) are ignored, seeinboxfor reference.
You can use selected email header data (e.g. Subject) to initialize additional
field values, seerir_field_namesattributedescriptionfor details.
rir_field_names
Zip attachment limits:
- the uncompressed size of the files within a.ziparchive may not exceed 40 MB
.zip
- only archives containing less than 1000 files are processed
- only files in the root of the archive are processed (or files inside a first level directory if it's the only one there)


## Export

In order to export extracted and confirmed data you can callexportendpoint. You can specify status, time-range
filters and annotation id list to limit returned results.
Export endpoint supports basic authentication to enable easy integration with
third-party systems.


## Auto-split of document

It is possible to process a single PDF file that contains several invoices.
Just insert a specialseparator pagebetween the documents. You can print this page and insert it between documents
while scanning.
Rossum will recognize a QR code on the page and split the PDF into individual documents
automatically. Produced documents are imported to the queue, while the original document
is set to asplitstate.
split


# Document Schema

Every queue has an associated schema that specifies which fields will be
extracted from documents as well as the structure of the data sent to
connector and exported from the platform.
Rossum schema supports data fields with single values (datapoint),
fields with multiple values (multivalue) or tuples of fields (tuple). At the
topmost level, each schema consists ofsections, which may either directly
contain actual data fields (datapoints) or use nestedmultivalues andtuples as
containers for single datapoints.
datapoint
multivalue
tuple
section
datapoints
multivalue
tuple
But while schema may theoretically consist of an arbitrary number of nested containers,
the Rossum UI supports only certain particular combinations of datapoint types.
The supported shapes are:simple:atomic datapoints of typenumber,string,dateorenumlist:simple datapoint within a multivaluetabular:simple datapoint within a "multivalue tuple" (a multivalue list containing a tuple for every row)
- simple:atomic datapoints of typenumber,string,dateorenum
number
string
date
enum
- list:simple datapoint within a multivaluetabular:simple datapoint within a "multivalue tuple" (a multivalue list containing a tuple for every row)
- tabular:simple datapoint within a "multivalue tuple" (a multivalue list containing a tuple for every row)


## Schema content

Schema content consists of a list ofsectionobjects.

### Common attributes

The following attributes are common for all schema objects:
AttributeTypeDescriptionRequiredcategorystringCategory of an object, one ofsection,multivalue,tupleordatapoint.yesidstringUnique identifier of an object. Maximum length is 50 characters.yeslabelstringUser-friendly label for an object, shown in the user interfaceyeshiddenbooleanIf set totrue, the object is not visible in the user interface, but remains stored in the database and may be exported. Default is false. Note thatsectionis hidden if all its children are hidden.nodisable_predictionbooleanCan be set totrueto disable field extraction, while still preserving the data shape. Ignored by aurora engines.no
section
multivalue
tuple
datapoint
true
section
true

### Section

Example of a section

```
{"category":"section","id":"amounts_section","label":"Amounts","children":[...],"icon":""}
```

{"category":"section","id":"amounts_section","label":"Amounts","children":[...],"icon":""}
Section represents a logical part of the document, such as amounts or vendor info.
It is allowed only at the top level. Schema allows multiple sections, and there should
be at least one section in the schema.
AttributeTypeDescriptionRequiredchildrenlist[object]Specifies objects grouped under a given section. It can containmultivalueordatapointobjects.yesiconstringThe icon that appears on the left panel in the UI for a given section (not yet supported on UI).
multivalue
datapoint

### Datapoint

A datapoint represents a single value, typically a field of a document or some global document information.
Fields common to all datapoint types:
AttributeTypeDescriptionRequiredtypestringData type of the object, must be one of the following:string,number,date,enum,buttonyescan_exportbooleanIf set tofalse, datapoint is not exported throughexport endpoint. Default is true.can_collapsebooleanIf set totrue, tabular (multivalue-tuple) datapoint may be collapsed in the UI. Default is false.rir_field_nameslist[string]List of references used to initialize an object value. Seebelowfor the description.default_valuestringDefault value used either for fields that do not use hints from AI engine predictions (i.e.rir_field_namesare not specified), or when the AI engine does not return any data for the field.constraintsobjectA map of various constraints for the field. SeeValue constraints.ui_configurationobjectA group of settings affecting behaviour of the field in the application. SeeUI configuration.widthintegerWidth of the column (in characters). Default widths are: number: 8, string: 20, date: 10, enum: 20. Only supported for table datapoints.stretchbooleanIf total width of columns doesn’t fill up the screen, datapoints with stretch set to true will be expanded proportionally to other stretching columns. Only supported for table datapoints.width_charsinteger(Deprecated) Usewidthandstretchproperties instead.score_thresholdfloat [0;1]Threshold used to automatically validate field content based onAI confidence scores. If not set,queue.default_score_thresholdis used.formulastring[0;2000]Formula definition, required only for fields of typeformula, seeFormula Fields.rir_field_namesshould also be empty for these fields.promptstring[0;2000]Prompt definition, required only for fields of typereasoning.contextlist[string]Context for the prompt, required only for fields of typereasoningseeLogical Types.
string
number
date
enum
button
false
true
rir_field_names
width
stretch
queue.default_score_threshold
formula
rir_field_names
reasoning
reasoning
rir_field_namesattribute allows to specify source of initial value of the object. List items may be:
rir_field_names
- one ofextracted field typesto use the AI engine prediction value
- upload:idto identify a value specified whileuploadingthe document
upload:id
- edit:idto identify a value specified inedit_pagesendpoint
edit:id
- email_header:<id>to use a value extracted from email headers. Supported email headers:from,to,reply-to,subject,message-id,date.
email_header:<id>
from
to
reply-to
subject
message-id
date
- email_body:<id>to select email body. Supported values aretext_htmlfor HTML body ortext_plainfor plain text body.
email_body:<id>
text_html
text_plain
- email:<id>to identify a value specified inemail.receivedhook response
email:<id>
email.received
- emails_import:<id>to identify a value specified in thevaluesparameter whenimporting an email.
emails_import:<id>
values
If more list items inrir_field_namesare specified, the first available value will be used.
rir_field_names

#### String type

Example string datapoint

```
{"category":"datapoint","id":"document_id","label":"Invoice ID","type":"string","default_value":null,"rir_field_names":["document_id"],"constraints":{"length":{"exact":null,"max":16,"min":null},"regexp":{"pattern":"^INV[0-9]+$"},"required":false}}
```

{"category":"datapoint","id":"document_id","label":"Invoice ID","type":"string","default_value":null,"rir_field_names":["document_id"],"constraints":{"length":{"exact":null,"max":16,"min":null},"regexp":{"pattern":"^INV[0-9]+$"},"required":false}}
String datapoint does not have any special attribute.

#### Date type

Example date datapoint

```
{"id":"item_delivered","type":"date","label":"Item Delivered","format":"MM/DD/YYYY","category":"datapoint"}
```

{"id":"item_delivered","type":"date","label":"Item Delivered","format":"MM/DD/YYYY","category":"datapoint"}
Attributes specific to Date datapoint:
AttributeTypeDescriptionRequiredformatstringEnforces a format fordatedatapoint on the UI. SeeDate formatbelow for more details. Default isYYYY-MM-DD.
date
YYYY-MM-DD
Date format supported:available tokens
Example date formats:
- D/M/YYYY: e.g. 23/1/2019
D/M/YYYY
- MM/DD/YYYY: e.g. 01/23/2019
MM/DD/YYYY
- YYYY-MM-DD: e.g. 2019-01-23 (ISO date format)
YYYY-MM-DD

#### Number type

Example number datapoint

```
{"id":"item_quantity","type":"number","label":"Quantity","format":"#,##0.#","category":"datapoint"}
```

{"id":"item_quantity","type":"number","label":"Quantity","format":"#,##0.#","category":"datapoint"}
Attributes specific to Number datapoint:
AttributeTypeDefaultDescriptionRequiredformatstring# ##0.#Available choices for number format show table below.nullvalue is allowed.aggregationsobjectA map of various aggregations for the field. Seeaggregations.
# ##0.#
null
The following table shows numeric formats with their examples.
FormatExample# ##0,#1 234,5 or 1234,5# ##0.#1 234.5 or 1234.5#,##0.#1,234.5 or 1234.5#'##0.#1'234.5 or 1234.5#.##0,#1.234,5 or 1234,5# ##01 234 or 1234#,##01,234 or 1234#'##01'234 or 1234#.##01.234 or 1234
# ##0,#
# ##0.#
#,##0.#
#'##0.#
#.##0,#
# ##0
#,##0
#'##0
#.##0
Example aggregations

```
{"id":"quantity","type":"number","label":"Quantity","category":"datapoint","aggregations":{"sum":{"label":"Total"}},"default_value":null,"rir_field_names":[]}
```

{"id":"quantity","type":"number","label":"Quantity","category":"datapoint","aggregations":{"sum":{"label":"Total"}},"default_value":null,"rir_field_names":[]}
Aggregations allow computation of some informative values, e.g. a sum of a table column with numeric values.
These are returned amongmessageswhen/v1/annotations/{id}/content/validateendpointis called.
Aggregations can be computed only for tables (multivaluesoftuples).
messages
/v1/annotations/{id}/content/validate
multivalues
tuples
AttributeTypeDescriptionRequiredsumobjectSum of values in a column. Defaultlabel: "Sum".
label
All aggregation objects can have an attributelabelthat will be shown in the UI.
label

#### Enum type

Example enum datapoint with options and enum_value_type

```
{"id":"document_type","type":"enum","label":"Document type","hidden":false,"category":"datapoint","options":[{"label":"Invoice Received","value":"21"},{"label":"Invoice Sent","value":"22"},{"label":"Receipt","value":"23"}],"default_value":"21","rir_field_names":[],"enum_value_type":"number"}
```

{"id":"document_type","type":"enum","label":"Document type","hidden":false,"category":"datapoint","options":[{"label":"Invoice Received","value":"21"},{"label":"Invoice Sent","value":"22"},{"label":"Receipt","value":"23"}],"default_value":"21","rir_field_names":[],"enum_value_type":"number"}
Attributes specific to Enum datapoint:
AttributeTypeDescriptionRequiredoptionsobjectSee object description below.yesenum_value_typestringData type of the option's value attribute. Must be one of the following:string,number,dateno
string
number
date
Every option consists of an object with keys:
AttributeTypeDescriptionRequiredvaluestringValue of the option.yeslabelstringUser-friendly label for the option, shown in the UI.yes
Enum datapoint value is matched in a case insensitive mode, e.g.EURcurrency value returned by the AI Core Engine is
matched successfully against{"value": "eur", "label": "Euro"}option.
EUR
{"value": "eur", "label": "Euro"}

#### Button type

Specifies a button shown in Rossum UI. For more details please refer tocustom UI extension.
Example button datapoint

```
{"id":"show_email","type":"button","category":"datapoint","popup_url":"http://example.com/show_customer_data","can_obtain_token":true}
```

{"id":"show_email","type":"button","category":"datapoint","popup_url":"http://example.com/show_customer_data","can_obtain_token":true}
Buttons cannot be direct children of multivalues (simple multivalues with buttons are not allowed. In tables, buttons are children of tuples).
Despite being a datapoint object, button currently cannot hold any value. Therefore, the set of available Button datapoint attributes is limited to:
AttributeTypeDescriptionRequiredtypestringData type of the object, must be one of the following:string,number,date,enum,buttonyescan_exportbooleanIf set tofalse, datapoint is not exported throughexport endpoint. Default is true.can_collapsebooleanIf set totrue, tabular (multivalue-tuple) datapoint may be collapsed in the UI. Default is false.popup_urlstringURL of a popup window to be opened when button is pressed.can_obtain_tokenbooleanIf set totruethe popup window is allowed to ask the main Rossum window for authorization token
string
number
date
enum
button
false
true
true

#### Value constraints

Example value constraints

```
{"id":"document_id","type":"string","label":"Invoice ID","category":"datapoint","constraints":{"length":{"max":32,"min":5},"required":false},"default_value":null,"rir_field_names":["document_id"]}
```

{"id":"document_id","type":"string","label":"Invoice ID","category":"datapoint","constraints":{"length":{"max":32,"min":5},"required":false},"default_value":null,"rir_field_names":["document_id"]}
Constraints limit allowed values. When constraints is not satisfied, annotation is considered invalid and cannot be exported.
AttributeTypeDescriptionRequiredlengthobjectDefines minimum, maximum or exact length for the datapoint value. By default, minimum and maximum are0and infinity, respectively. Supported attributes:min,maxandexactregexpobjectWhen specified, content must match a regular expression. Supported attributes:pattern. To ensure that entire value matches, surround your regular expression with^and$.requiredbooleanSpecifies if the datapoint is required by the schema. Default value istrue.
0
min
max
exact
pattern
^
$
true

#### UI configuration

Example UI configuration

```
{"id":"document_id","type":"string","label":"Invoice ID","category":"datapoint","ui_configuration":{"type":"captured","edit":"disabled"},"default_value":null,"rir_field_names":["document_id"]}
```

{"id":"document_id","type":"string","label":"Invoice ID","category":"datapoint","ui_configuration":{"type":"captured","edit":"disabled"},"default_value":null,"rir_field_names":["document_id"]}
UI configuration provides a group of settings, which alter behaviour of the field in the application. This does not affect behaviour of the field via the API.
For example, disablingeditprohibits changing a value of the datapoint in the application, but the value can still be modified through API.
edit
AttributeTypeDescriptionRequiredtypestringLogical type of the datapoint. Possible values are:captured,data,manual,formula,reasoningornull. Default value isnull.falseeditstringWhen set todisabled, value of the datapoint is not editable via UI. When set toenabled_without_warning, no warnings are displayed in the UI regarding this fields editing behaviour. Default value isenabled, this option enables field editing, but user receives dismissible warnings when doing so.false
captured
data
manual
formula
reasoning
null
null
disabled
enabled_without_warning
enabled
- Captured fieldrepresents information retrieved by the OCR model. If combined witheditoption disabled, user can't overwrite field's value, but is able to redraw field's bounding box and select another value from the document by such an action.
edit
- Data fieldrepresents information filled by extensions. This field is not mapped to the AI model, so it does not have a bounding box, neither it's possible to create one. If combined witheditoption disabled the field can't be modified from the UI.
edit
- Manual fieldbehaves exactly likeData field, without the mapping to extensions. This field should be used for sharing information between users or to transfer information to downstream systems.
- Formula fieldThis field will be updated according to itsformuladefinition, seeFormula Fields. If theeditoption is not disabled the field value can be overridden from the UI (seeno_recalculation).
formula
edit
- Reasoning fieldsThis field will be updated according to itspromptandcontext.contextsupports adding related schema fields in a format of TxScript strings (e.g.field.invoice_id, alsoself.attr.labelandself.attr.descriptionare supported). If theeditoption is not disabled the field value can be overridden from the UI (seeno_recalculation).
prompt
context
context
field.invoice_id
self.attr.label
self.attr.description
edit
- nullvalue is displayed in UI asUnsetand behaves similar to theCaptured field.

### Multivalue

Example of a multivalue:

```
{"category":"multivalue","id":"line_item","label":"Line Item","children":{...},"show_grid_by_default":false,"min_occurrences":null,"max_occurrences":null,"rir_field_names":null}
```

{"category":"multivalue","id":"line_item","label":"Line Item","children":{...},"show_grid_by_default":false,"min_occurrences":null,"max_occurrences":null,"rir_field_names":null}
Example of a multivalue with grid row-types specification:

```
{"category":"multivalue","id":"line_item","label":"Line Item","children":{...},"grid":{"row_types":["header","data","footer"],"default_row_type":"data","row_types_to_extract":["data"]},"min_occurrences":null,"max_occurrences":null,"rir_field_names":["line_items"]}
```

{"category":"multivalue","id":"line_item","label":"Line Item","children":{...},"grid":{"row_types":["header","data","footer"],"default_row_type":"data","row_types_to_extract":["data"]},"min_occurrences":null,"max_occurrences":null,"rir_field_names":["line_items"]}
Multivalue is list ofdatapoints ortuples of the same type.
It represents a container for data with multiple occurrences
(such as line items) and can contain only objects with the sameid.
datapoint
tuple
id
AttributeTypeDescriptionRequiredchildrenobjectObject specifying type of children. It can contain only objects with categoriestupleordatapoint.yesmin_occurrencesintegerMinimum number of occurrences of nested objects. If condition of min_occurrences is violated corresponding fields should be manually reviewed. Minimum required value for the field is 0. If not specified, it is set to 0 by default.max_occurrencesintegerMaximum number of occurrences of nested objects. All additional rows above max_occurrences are removed by extraction process. Minimum required value for the field is 1. If not specified, it is set to 1000 by default.gridobjectConfigure magic-grid feature properties, seebelow.show_grid_by_defaultbooleanIf set totrue, the magic-grid is opened instead of footer upon entering the multivalue. Defaultfalse. Applied only in UI. Useful when annotating documents for custom training.rir_field_nameslist[string]List of names used to initialize content from the AI engine predictions. If specified, the value of the first field from the array is used, otherwise default nameline_itemsis used. Attribute can be set only for multivalue containing objects with categorytuple.no
tuple
datapoint
true
false
line_items
tuple

#### Multivalue grid object

Multivaluegridobject allows to specify arow typefor each row of the
grid. For data representation of actual grid data rows seeGrid object description.
grid
AttributeTypeDescriptionDefaultRequiredrow_typeslist[string]List of allowed row type values.["data"]yesdefault_row_typestringRow type to be used by defaultdatayesrow_types_to_extractlist[string]Types of rows to be extracted to related table["data"]yes
["data"]
data
["data"]
For example to distinguish two header types and a footer in the validation interface, following row types may be used:header,subsection_header,dataandfooter.
header
subsection_header
data
footer
Currently, data extraction classifies every row as eitherdataorheader(additional row types may be introduced
in the future). We remove rows returned by data extraction that are not inrow_typeslist (e.g.headerby
default) and are on the top/bottom of the table. When they are in the middle of the table, we mark them as skipped
(null).
data
header
row_types
header
null
There are three visual modes, based onrow_typesquantity:
row_types
- More than two row types defined: User selects row types freely to any non-default row type. Clearing row type resets to a default row type. We support up to 6 colors to easily distinguish row types visually.
- Two row types defined (header and default): User only marks header and skipped rows. Clearing row type resets to a default row type.
- One row type defined: User is only able to mark row as skipped (nullvalue in data). This is also a default behavior when nogridrow types configuration is specified in the schema.
null
grid
row_types_to_extract

### Tuple

Example of a tuple:

```
{"category":"tuple","id":"tax_details","label":"Tax Details","children":[...],"rir_field_names":["tax_details"]}
```

{"category":"tuple","id":"tax_details","label":"Tax Details","children":[...],"rir_field_names":["tax_details"]}
Container representing tabular data with related values, such as tax details.
Atuplemust be nested within amultivalueobject, but unlikemultivalue,
it may consist of objects with differentids.
tuple
multivalue
multivalue
id
AttributeTypeDescriptionRequiredchildrenlist[object]Array specifying objects that belong to a giventuple. It can contain only objects with categorydatapoint.yesrir_field_nameslist[string]List of names used to initialize content from the AI engine predictions. If specified, the value of the first extracted field from the array is used, otherwise, no AI engine initialization is done for the object.
tuple
datapoint


## Updating Schema

When project evolves, it is a common practice to enhance or change the extracted
field set. This is done by updating theschema object.
By design, Rossum supports multiple schema versions at the same time. However,
each document annotation is related to only one of those schemas. If the schema
is updated, all related document annotations are updated accordingly. Seepreserving data on schema changebelow for
limitations of schema updates.
In addition, everyqueueis linked to a schema, which is used for all newly
imported documents.
When updating a schema, there are two possible approaches:
- Update the schema object (PUT/PATCH). All related annotations will be
updated to match current schema shape (evenexportedanddeleteddocuments).
exported
deleted
- Create a new schema object (POST) and link it to the queue. In such case,
only newly created objects will use the current schema. All previously
created objects will remain in the shape of their linked schema.
Use case 1 - Initial setting of a schema
- Situation: User is initially setting up the schema. This might be an iterative process.
- Recommendation: Edit the existing schema byupdating schema(PUT) orupdating part of a schema(PATCH).
Use case 2 - Updating attributes of a field (label, constraints, options, etc.)
- Situation: User is updating field, e.g. changing label, number format, constraints, enum options, hidden flag, etc.
- Recommendation: Edit existing schema (see Use case 1).
Use case 3 - Adding new field to a schema, even for already imported documents.
- Situation: User is extending a production schema by adding a new field. Moreover, user would like to see all annotations (to_review,postponed,exported,deleted, etc. states) in the look of the newly extended schema.
to_review
postponed
exported
deleted
- Recommendation: Edit existing schema (see Use case 1). Data of already created annotations will be transformed to the shape of the updated schema. New fields of annotations into_reviewandpostponedstate that are linked toextracted fields typeswill be filled byAI Engine, if available. New fields for alreadyexportedordeletedannotations (alsopurged,exportingandfailed_export) will be filled with empty or default values.
to_review
postponed
exported
deleted
purged
exporting
failed_export
Use case 4 - Adding new field to schema, only for newly imported documents
- Situation: User is extending a production schema by adding a new field. However, with the intention that the user does not want to see the newly added field on previously created annotations.
- Recommendation:Create a new schema object(POST) and link it to the queue. Annotation data of previously created annotations will be preserved according to the original schema. This approach is recommended if there is an organizational need to keep different field sets before and after the schema update.
Use case 5 - Deleting schema field, even for already imported documents.
- Situation: User is changing a production schema by removing a field that was used previously. However, user would like to see all annotations (to_review,postponed,exported,deleted, etc. states) in the look of the newly extended schema. There is no need to see the original fields in already exported annotations.
to_review
postponed
exported
deleted
- Recommendation: Edit existing schema (see Use case 1).
Use case 6 - Deleting schema field, only for newly imported documents
- Situation: User is changing a production schema by removing a field that was used previously. However, with the intention that the user will still be able to see the removed fields on previously created annotations.
- Recommendation: Create a new schema object (see Use case 4). Annotation data of previously created annotations will be preserved according to the original schema. This approach is recommended if there is an organizational need to retrieve the data in the original state.

### Preserving data on schema change

In order to transfer annotation fieldvaluesproperly during the schema update,
a datapoint'scategoryandschema_idmust be preserved.
category
schema_id
Supported operations that preserve fields values are:
- adding a new datapoint (filled fromAI Engine, if available)
- reordering datapoints on the same level
- moving datapoints from section to another section
- moving datapoints to and from a tuple
- reordering datapoints inside a tuple
- making datapoint a multivalue (original datapoint is the only value in a new multivalue container)
- making datapoint non-multivalue (only first datapoint value is preserved)


## Extracted field types

AI engine currently automatically extracts the following fields at theallendpoint, subject to ongoing expansion.
all

### Identifiers

Example of a schema with different identifiers:

```
[{"category":"section","children":[{"category":"datapoint","constraints":{"required":false},"default_value":null,"id":"document_id","label":"Invoice number","rir_field_names":["document_id"],"type":"string"},{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"D/M/YYYY","id":"date_issue","label":"Issue date","rir_field_names":["date_issue"],"type":"date"},{"category":"datapoint","constraints":{"required":false},"default_value":null,"id":"terms","label":"Terms","rir_field_names":["terms"],"type":"string"}],"icon":null,"id":"invoice_info_section","label":"Basic information"}]
```

[{"category":"section","children":[{"category":"datapoint","constraints":{"required":false},"default_value":null,"id":"document_id","label":"Invoice number","rir_field_names":["document_id"],"type":"string"},{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"D/M/YYYY","id":"date_issue","label":"Issue date","rir_field_names":["date_issue"],"type":"date"},{"category":"datapoint","constraints":{"required":false},"default_value":null,"id":"terms","label":"Terms","rir_field_names":["terms"],"type":"string"}],"icon":null,"id":"invoice_info_section","label":"Basic information"}]
Attr. rir_field_namesField labelDescriptionaccount_numBank AccountBank account number. Whitespaces are stripped.bank_numSort CodeSort code. Numerical code of the bank.ibanIBANBank account number in IBAN format.bicBIC/SWIFTBank BIC or SWIFT code.const_symConstant SymbolStatistical code on payment order.spec_symSpecific SymbolPayee id on the payment order, or similar.var_symVariable symbolIn some countries used by the supplier to match the payment received against the invoice. Possible non-numeric characters are stripped.termsTermsPayment terms as written on the document (e.g. "45 days", "upon receipt").payment_methodPayment methodPayment method defined on a document (e.g. 'Cheque', 'Pay order', 'Before delivery')customer_idCustomer NumberThe number by which the customer is registered in the system of the supplier. Whitespaces are stripped.date_dueDate DueThe due date of the invoice.date_issueIssue DateDate of issue of the document.date_uzpTax Point DateThe date of taxable event.document_idDocument IdentifierDocument number. Whitespaces are stripped.order_idOrder NumberPurchase order identification (Order Numbers not captured as "sender_order_id"). Whitespaces are stripped.recipient_addressRecipient AddressAddress of the customer.recipient_dicRecipient Tax NumberTax identification number of the customer. Whitespaces are stripped.recipient_icRecipient Company IDCompany identification number of the customer. Possible non-numeric characters are stripped.recipient_nameRecipient NameName of the customer.recipient_vat_idRecipient VAT NumberCustomer VAT Numberrecipient_delivery_nameRecipient Delivery NameName of the recipient to whom the goods will be delivered.recipient_delivery_addressRecipient Delivery AddressAddress of the reciepient where the goods will be delivered.sender_addressSupplier AddressAddress of the supplier.sender_dicSupplier Tax NumberTax identification number of the supplier. Whitespaces are stripped.sender_icSupplier Company IDBusiness/organization identification number of the supplier. Possible non-numeric characters are stripped.sender_nameSupplier NameName of the supplier.sender_vat_idSupplier VAT NumberVAT identification number of the supplier.sender_emailSupplier EmailEmail of the sender.sender_order_idSupplier's Order IDInternal order ID in the suppliers system.delivery_note_idDelivery Note IDDelivery note ID defined on the invoice.supply_placePlace of SupplyPlace of supply (the name of the city or state where the goods will be supplied).
invoice_id
document_id
invoice_id
document_id

### Document attributes

Attr. rir_field_namesField labelDescriptioncurrencyCurrencyThe currency which the invoice is to be paid in. Possible values: AED, ARS, AUD, BGN, BRL, CAD, CHF, CLP, CNY, COP, CRC, CZK, DKK, EUR, GBP, GTQ, HKD, HUF, IDR, ILS, INR, ISK, JMD, JPY, KRW, MXN, MYR, NOK, NZD, PEN, PHP, PLN, RON, RSD, SAR, SEK, SGD, THB, TRY, TWD, UAH, USD, VES, VND, ZAR or other. May be also in lowercase.document_typeDocument TypePossible values: credit_note, debit_note, tax_invoice (most typical), proforma, receipt, delivery_note, order or other.languageLanguageThe language which the document was written in. Values are ISO 639-3 language codes, e.g.: eng, fra, deu, zho. SeeLanugages Supported By Rossumpayment_method_typePayment Method TypePayment method used for the transaction. Possible values: card, cash.
invoice_type
document_type
invoice_type
document_type

### Amounts

Attr. rir_field_namesField labelDescriptionamount_dueAmount DueFinal amount including tax to be paid after deducting all discounts and advances.amount_roundingAmount RoundingRemainder after rounding amount_total.amount_totalTotal AmountSubtotal over all items, including tax.amount_paidAmount paidAmount paid already.amount_total_baseTax Base TotalBase amount for tax calculation.amount_total_taxTax TotalTotal tax amount.
Typical relations (may depend on local laws):

```
amount_total = amount_total_base + amount_total_tax
amount_rounding = amount_total - round(amount_total)
amount_due = amount_total - amount_paid + amount_rounding
```

All amounts are in the main currency of the invoice (as identified in the currency response field).
Amounts in other currencies are generally excluded.

### Tables

At the moment, the AI engine automatically extracts 2 types of tables.
In order to pick one of the possible choices, setrir_field_namesattribute onmultivalue.
rir_field_names
multivalue
Attr. rir_field_namesTabletax_detailsTax detailsline_itemsLine items
rir_field_names
multivalue
line_items
rir_field_names
tax_detail_
tax_details

#### Tax details

Example of a tax details table:

```
{"category":"section","children":[{"category":"multivalue","children":{"category":"tuple","children":[{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"# ##0.#","id":"vat_detail_rate","label":"VAT rate","rir_field_names":["tax_detail_rate"],"type":"number","width":15},...],"id":"vat_detail","label":"VAT detail"},"default_value":null,"id":"vat_details","label":"VAT details","max_occurrences":null,"min_occurrences":null,"rir_field_names":["tax_details"]}],"icon":null,"id":"amounts_section","label":"Amounts section"}
```

{"category":"section","children":[{"category":"multivalue","children":{"category":"tuple","children":[{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"# ##0.#","id":"vat_detail_rate","label":"VAT rate","rir_field_names":["tax_detail_rate"],"type":"number","width":15},...],"id":"vat_detail","label":"VAT detail"},"default_value":null,"id":"vat_details","label":"VAT details","max_occurrences":null,"min_occurrences":null,"rir_field_names":["tax_details"]}],"icon":null,"id":"amounts_section","label":"Amounts section"}
Tax details table and breakdown by tax rates.
Attr. rir_field_namesField labelDescriptiontax_detail_baseTax BaseSum of tax bases for items with the same tax rate.tax_detail_rateTax RateOne of the tax rates in the tax breakdown.tax_detail_taxTax AmountSum of taxes for items with the same tax rate.tax_detail_totalTax TotalTotal amount including tax for all items with the same tax rate.tax_detail_codeTax Code[BETA]Text on document describing tax code of the tax rate (e.g. 'GST', 'CGST', 'DPH', 'TVA'). If multiple tax rates belong to one tax code on the document, the tax code will be assigned only to the first tax rate. (in future such tax code will be distributed to all matching tax rates.)

#### Line items

Example of a line items table:

```
{"category":"section","children":[{"category":"multivalue","children":{"category":"tuple","children":[{"category":"datapoint","constraints":{"required":true},"default_value":null,"id":"item_desc","label":"Description","rir_field_names":["table_column_description"],"type":"string","stretch":true},{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"# ##0.#","id":"item_quantity","label":"Quantity","rir_field_names":["table_column_quantity"],"type":"number","width":15},{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"# ##0.#","id":"item_amount_total","label":"Price w tax","rir_field_names":["table_column_amount_total"],"type":"number"}],"id":"line_item","label":"Line item","rir_field_names":[]},"default_value":null,"id":"line_items","label":"Line item","max_occurrences":null,"min_occurrences":null,"rir_field_names":["line_items"]}],"icon":null,"id":"line_items_section","label":"Line items"}
```

{"category":"section","children":[{"category":"multivalue","children":{"category":"tuple","children":[{"category":"datapoint","constraints":{"required":true},"default_value":null,"id":"item_desc","label":"Description","rir_field_names":["table_column_description"],"type":"string","stretch":true},{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"# ##0.#","id":"item_quantity","label":"Quantity","rir_field_names":["table_column_quantity"],"type":"number","width":15},{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"# ##0.#","id":"item_amount_total","label":"Price w tax","rir_field_names":["table_column_amount_total"],"type":"number"}],"id":"line_item","label":"Line item","rir_field_names":[]},"default_value":null,"id":"line_items","label":"Line item","max_occurrences":null,"min_occurrences":null,"rir_field_names":["line_items"]}],"icon":null,"id":"line_items_section","label":"Line items"}
AI engine currently automatically extracts line item table content and recognizes row and column types as detailed below.
Invoice line items come in a wide variety of different shapes and forms. The current implementation can deal with
(or learn) most layouts, with borders or not, different spacings, header rows, etc. We currently make
two further assumptions:
- The table generally follows a grid structure - that is, columns and rows may be represented as rectangle spans.
In practice, this means that we may currently cut off text that overlaps from one cell to the next column.
We are also not optimizing for table rows that are wrapped to multiple physical lines.
- The table contains just a flat structure of line items, without subsection headers, nested tables, etc.
We plan to gradually remove both assumptions in the future.
Attribute rir_field_namesField labelDescriptiontable_column_codeItem Code/IdCan be the SKU, EAN, a custom code (string of letters/numbers) or even just the line number.table_column_descriptionItem DescriptionLine item description. Can be multi-line with details.table_column_quantityItem QuantityQuantity of the item.table_column_uomItem Unit of MeasureUnit of measure of the item (kg, container, piece, gallon, ...).table_column_rateItem RateTax rate for the line item.table_column_taxItem TaxTax amount for the line. Rule of thumb:tax = rate * amount_base.table_column_amount_baseAmount BaseUnit price without tax. (This is the primary unit price extracted.)table_column_amountAmountUnit price with tax. Rule of thumb:amount = amount_base + tax.table_column_amount_total_baseAmount Total BaseThe total amount to be paid for all the items excluding the tax. Rule of thumb:amount_total_base = amount_base * quantity.table_column_amount_totalAmount TotalThe total amount to be paid for all the items including the tax. Rule of thumb:amount_total = amount * quantity.table_column_otherOtherUnrecognized data type.
tax = rate * amount_base
amount = amount_base + tax
amount_total_base = amount_base * quantity
amount_total = amount * quantity


# Annotation Lifecycle

When a document is submitted to Rossum within a given queue, anannotation objectis assigned to it.
An annotation goes through a variety of states as it is processed, and eventually exported.
StateDescriptioncreatedAnnotation was created manually via POST to annotations endpoint. Annotation created this way may be switched toimportingstate only at the end of theupload.createdevent (this happens automatically).importingDocument is being processed by theAI Enginefor data extraction.failed_importImport failed e.g. due to a malformed document file.splitAnnotation was split in user interface or via API and new annotations were created from it.to_reviewInitial extraction step is done and the annotation is waiting for user validation.reviewingAnnotation is undergoing validation in the user interface.in_workflowAnnotation is being processed in a workflow. Annotation content cannot be modified while in this state. Please note that any manual interaction with this status may introduce confilicts with Rossum automated workflows. Read more about Rossum Workflowshere.confirmedAnnotation is validated and confirmed by the user. This status must be explicitly enabled on thequeueto be present.rejectedAnnotation was rejected by user. This status must be explicitly enabled on thequeueto be present. You can read about when a rejection is possiblehere.exportingAnnotation is validated and is now awaiting the completion of connector save call. Seeconnector extensionfor more information on this status.exportedAnnotation is validated and successfully passed all hooks; this is the typical terminal state of an annotation.failed_exportWhen the connector returned an error.postponedOperator has chosen to postpone the annotation instead of exporting it.deletedWhen the annotation was deleted by the user.purgedOnly metadata was preserved after a deletion. This status is terminal and cannot be further changed. Seepurge deletedif you want to know how to purge an annotation.
importing
upload.created
This diagram shows exact flow between the annotation states whole working with the UI.


# Usage report

In order to obtain an overview of the Rossum usage, you can download Csv file
with basic Rossum statistics.
The statistics contains following attributes:
- Username (may be empty in case document was not modified by any user)
- Workspace name
- Queue name
- User url
- Queue url
- Workspace url
- Imported: count of all documents that were imported during the time period
- Confirmed: count of all documents that were confirmed during the time period
- Rejected: count of all documents that were rejected during the time period
- Rejected automatically: count of all documents that were automatically rejected during the time period
- Rejected manually: count of all documents that were manually rejected during the time period
- Deleted: count of documents that were deleted during the time period
- Exported: count of documents that were successfully exported during the time period
- Net time: total time spent by a user validating the successfully exported documents
Download usage statistics (January 2019).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/annotations/usage_report?from=2019-01-01&to=2019-01-31'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/annotations/usage_report?from=2019-01-01&to=2019-01-31'
Csv file (csv) may be downloaded fromhttps://<example>.rossum.app/api/v1/annotations/usage_report?format=csv.
https://<example>.rossum.app/api/v1/annotations/usage_report?format=csv
You may specify date range usingfromandtoparameters (inclusive). If not
specified, a report for last 12 months is generated.
from
to
admin
manager

### Request

POST /v1/annotations/usage_report
POST /v1/annotations/usage_report
AttributeTypeDescriptionfilterobjectFilters to be applied on documents used for the computation of usage reportfilter.userslist[URL]Filter documents modified by the specified users (not applied toimported_count)filter.queueslist[URL]Filter documents from the specified queuesfilter.begin_datedatetimeFilter documents that has date (arrived_atforimported_count;deleted_atfordeleted_count;rejected_atforrejected_count; orexported_atfor the rest)greaterthan specified.filter.end_datedatetimeFilter documents that has date (arrived_atforimported_count;deleted_atfordeleted_count;rejected_atforrejected_count; orexported_atfor the rest)lowerthan specified.exported_on_time_threshold_sfloatThreshold (in seconds) under which are documents denoted ason_time.group_bylist[string]List of attributes by which theseriesis to be grouped. Possible values:user,workspace,queue,month,week,day.
imported_count
arrived_at
imported_count
deleted_at
deleted_count
rejected_at
rejected_count
exported_at
arrived_at
imported_count
deleted_at
deleted_count
rejected_at
rejected_count
exported_at
on_time
series
user
workspace
queue
month
week
day

```
{"filter":{"users":["https://<example>.rossum.app/api/v1/users/173"],"queues":["https://<example>.rossum.app/api/v1/queues/8199"],"begin_date":"2019-12-01","end_date":"2020-01-31"},"exported_on_time_threshold_s":86400,"group_by":["user","workspace","queue","month"]}
```

{"filter":{"users":["https://<example>.rossum.app/api/v1/users/173"],"queues":["https://<example>.rossum.app/api/v1/queues/8199"],"begin_date":"2019-12-01","end_date":"2020-01-31"},"exported_on_time_threshold_s":86400,"group_by":["user","workspace","queue","month"]}
admin
manager

### Response

Status:200
200

```
{"series":[{"begin_date":"2019-12-01","end_date":"2020-01-01","queue":"https://<example>.rossum.app/api/v1/queues/8199","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","values":{"imported_count":2,"confirmed_count":6,"rejected_count":2,"rejected_automatically_count":1,"rejected_manually_count":1,"deleted_count":null,"exported_count":null,"turnaround_avg_s":null,"corrections_per_document_avg":null,"exported_on_time_count":null,"exported_late_count":null,"time_per_document_avg_s":null,"time_per_document_active_avg_s":null,"time_and_corrections_per_field":[]}},{"begin_date":"2020-01-01","end_date":"2020-02-01","queue":"https://<example>.rossum.app/api/v1/queues/8199","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","user":"https://<example>.rossum.app/api/v1/users/173","values":{"imported_count":null,"confirmed_count":6,"rejected_count":3,"rejected_automatically_count":2,"rejected_manually_count":1,"deleted_count":2,"exported_count":2,"turnaround_avg_s":1341000,"corrections_per_document_avg":1.0,"exported_on_time_count":1,"exported_late_count":1,"time_per_document_avg_s":70.0,"time_per_document_active_avg_s":50.0,"time_and_corrections_per_field":[{"schema_id":"date_due","label":"Date due","total_count":1,"corrected_ratio":0.0,"time_spent_avg_s":0.0},...]}},...],"totals":{"imported_count":7,"confirmed_count":6,"rejected_count":5,"rejected_automatically_count":3,"rejected_manually_count":2,"deleted_count":2,"exported_count":3,"turnaround_avg_s":894000,"corrections_per_document_avg":1.0,"exported_on_time_count":2,"exported_late_count":1,"time_per_document_avg_s":70.0,"time_per_document_active_avg_s":50.0}}
```

{"series":[{"begin_date":"2019-12-01","end_date":"2020-01-01","queue":"https://<example>.rossum.app/api/v1/queues/8199","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","values":{"imported_count":2,"confirmed_count":6,"rejected_count":2,"rejected_automatically_count":1,"rejected_manually_count":1,"deleted_count":null,"exported_count":null,"turnaround_avg_s":null,"corrections_per_document_avg":null,"exported_on_time_count":null,"exported_late_count":null,"time_per_document_avg_s":null,"time_per_document_active_avg_s":null,"time_and_corrections_per_field":[]}},{"begin_date":"2020-01-01","end_date":"2020-02-01","queue":"https://<example>.rossum.app/api/v1/queues/8199","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","user":"https://<example>.rossum.app/api/v1/users/173","values":{"imported_count":null,"confirmed_count":6,"rejected_count":3,"rejected_automatically_count":2,"rejected_manually_count":1,"deleted_count":2,"exported_count":2,"turnaround_avg_s":1341000,"corrections_per_document_avg":1.0,"exported_on_time_count":1,"exported_late_count":1,"time_per_document_avg_s":70.0,"time_per_document_active_avg_s":50.0,"time_and_corrections_per_field":[{"schema_id":"date_due","label":"Date due","total_count":1,"corrected_ratio":0.0,"time_spent_avg_s":0.0},...]}},...],"totals":{"imported_count":7,"confirmed_count":6,"rejected_count":5,"rejected_automatically_count":3,"rejected_manually_count":2,"deleted_count":2,"exported_count":3,"turnaround_avg_s":894000,"corrections_per_document_avg":1.0,"exported_on_time_count":2,"exported_late_count":1,"time_per_document_avg_s":70.0,"time_per_document_active_avg_s":50.0}}
The response consists of two parts:totalsandseries.
totals
series

### Totals

Totalscontain summary information for the whole period (betweenbegin_dateandend_date).
Totals
begin_date
end_date
AttributeTypeDescriptionimported_countintCount of documents that were uploaded to Rossumconfirmed_countintCount of documents that were confirmedrejected_countintCount of documents that were rejectedrejected_automatically_countintCount of documents that were automatically rejectedrejected_manually_countintCount of documents that were manually rejecteddeleted_countintCount of documents that were deletedexported_countintCount of documents that were successfully exportedturnaround_avg_sfloatAverage time (in seconds) that a document spends in Rossum (computed as timeexported_at-arrived_at)corrections_per_document_avgfloatAverage count of corrections on documentsexported_on_time_countintNumber of documents of whichturnaroundwasunderexported_on_time_thresholdexported_late_countintNumber of documents of whichturnaroundwasaboveexported_on_time_thresholdtime_per_document_avg_sfloatAverage time (in seconds) that users spent validating documents. Based on thetime_spent_overallmetric, seeannotation processing durationtime_per_document_active_avg_sfloatAverage active time (in seconds) that users spent validating documents. Based on thetime_spent_activemetric, seeannotation processing duration
exported_at
arrived_at
turnaround
exported_on_time_threshold
turnaround
exported_on_time_threshold
time_spent_overall
time_spent_active

### Series

Seriescontain information grouped by fields defined ingroup_by.
The data (seeabove) are wrapped invaluesobject,
and accompanied by the values of attributes that were used for grouping.
Series
group_by
values
AttributeTypeDescriptionuserURLUser, who modified documents within the groupworkspaceURLWorkspace, in which are the documents within the groupqueueURLQueue, in which are the documents within the groupbegin_datedateStart date, of the documents within the groupend_datedateFinal date, of the documents within the groupvaluesobjectContains the data oftotalsandtime_and_corrections_per_fieldlist (for details seebelow).
totals
time_and_corrections_per_field
In addition to thetotalsdata,seriescontaintime_and_corrections_per_fieldlist
that provides detailed data about statistics on each field.
totals
series
time_and_corrections_per_field

#### Series details

The detail object contains statistics grouped per field (schema_id).
schema_id
AttributeTypeDescriptionschema_idstringReference mapping of thedata objectto the schema treelabelstringLabel of the data object (taken from schema).total_countintNumber of data objectscorrected_ratio*float [0;1]Ratio of data objects that must have been corrected after automatic extraction.time_spent_avg_sfloatAverage time (in seconds) spent on validating the data objects
*Corrected ratio is calculated based on human corrections. If any kind of automation (Hook, Webhook, etc) is ran on the datapoints, even after a human correction took a place, the corrected_ration will not be calculated -> Is set to 0.


# Extensions

The Rossum platform may be extended via third-party, externally running
services or custom serverless functions. These extensions are registered to receive
callbacks from the Rossum platform on various occasions and allow to modify
the platform behavior. Currently we support these callback extensions:Webhooks,Serverless Functions,
andConnectors.
Webhooks and connectors require a third-party service accessible through an HTTP
endpoint. This may incur additional operational and implementation costs.
User-definedserverless functions, on the
contrary, are executed within Rossum platform and no additional setup is
necessary. They share the interface (input and output data format, error
handling) with webhooks.
See theBuilding Your Own Extensionset of guides in Rossum's developer portal for an introduction to Rossum extensions.


## Webhook Extension

The webhook component is the most flexible extension. It covers all the most frequent use cases:
- displaying messages to users in validation screen,
- applying custom business rules to check, change, or autofill missing values,
- reacting to document status change in your workflow,
- sending reviewed data to an external systems.

### Implement a webhook

Webhooks are designed to be implemented using a push-model using common HTTPS
protocol. When an event is triggered, the webhook endpoint is called with a relevant request payload.
The webhook must be deployed with a public IP address so that the Rossum platform
can call its endpoints; for testing, a middleware likengrokorserveomay come useful.
- Simple custom checkexample (JavaScript)
- Vendor matchingexample (Python)
- Schema changeexample (Python)

### Webhook vs. Connector

Webhook extensions are similar toconnectors, but they
are more flexible and easier to use. A webhook is notified when a defined type
ofwebhook eventoccurs for a related queue.
Advantages of webhooks over connectors:
- There may be multiple webhooks defined for a single queue
- No hard-coded endpoint names (/validate,/save)
/validate
/save
- Robust retry mechanism in case of webhook failure
- If webhooks are connected via therun_afterparameter, the results from the predecessor webhook are passed to its successor
run_after
Webhooks are defined using ahookobject of typewebhook. For a description
how to create and manage hooks, see theHook API.
hook

### Webhook Events

Example data sent forannotation_statusevent to thehook.config.urlwhen status of the annotation changes
annotation_status

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/789","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"my-rossum-importer","password":"secret-importer-user-password"},"action":"changed","event":"annotation_status","annotation":{"document":"https://<example>.rossum.app/api/v1/documents/314621","id":314521,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/223","pages":["https://<example>.rossum.app/api/v1/pages/551518"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","previous_status":"importing","rir_poll_id":"54f6b91cfb751289e71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/314521","content":"https://<example>.rossum.app/api/v1/annotations/314521/content","time_spent":0,"metadata":{},"organization":"https://<example>.rossum.app/api/v1/organizations/1"},"document":{"id":314621,"url":"https://<example>.rossum.app/api/v1/documents/314621","s3_name":"272c2f41ae84a4f19a422cb432a490bb","mime_type":"application/pdf","arrived_at":"2019-02-06T23:04:00.933658Z","original_file_name":"test_invoice_1.pdf","content":"https://<example>.rossum.app/api/v1/documents/314621/content","metadata":{}}}
```

{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/789","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"my-rossum-importer","password":"secret-importer-user-password"},"action":"changed","event":"annotation_status","annotation":{"document":"https://<example>.rossum.app/api/v1/documents/314621","id":314521,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/223","pages":["https://<example>.rossum.app/api/v1/pages/551518"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","previous_status":"importing","rir_poll_id":"54f6b91cfb751289e71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/314521","content":"https://<example>.rossum.app/api/v1/annotations/314521/content","time_spent":0,"metadata":{},"organization":"https://<example>.rossum.app/api/v1/organizations/1"},"document":{"id":314621,"url":"https://<example>.rossum.app/api/v1/documents/314621","s3_name":"272c2f41ae84a4f19a422cb432a490bb","mime_type":"application/pdf","arrived_at":"2019-02-06T23:04:00.933658Z","original_file_name":"test_invoice_1.pdf","content":"https://<example>.rossum.app/api/v1/documents/314621/content","metadata":{}}}
Example data sent forannotation_contentevent to thehook.config.urlwhen user updates a value in UI
annotation_content

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/781","settings":{"example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"password":"secret-importer-user-password"},"action":"updated","event":"annotation_content","annotation":{"document":"https://<example>.rossum.app/api/v1/documents/314621","id":314521,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/223","pages":["https://<example>.rossum.app/api/v1/pages/551518"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","previous_status":"importing","rir_poll_id":"54f6b91cfb751289e71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/314521","organization":"https://<example>.rossum.app/api/v1/organizations/1","content":[{"id":1123123,"url":"https://<example>.rossum.app/api/v1/annotations/314521/content/1123123","schema_id":"basic_info","category":"section","children":[{"id":20456864,"url":"https://<example>.rossum.app/api/v1/annotations/1/content/20456864","content":{"value":"18 492.48","normalized_value":"18492.48","page":2,...},"category":"datapoint","schema_id":"number","validation_sources":["checks","score"],"time_spent":0}]}],"time_spent":0,"metadata":{}},"document":{"id":314621,"url":"https://<example>.rossum.app/api/v1/documents/314621","s3_name":"272c2f41ae84a4f19a422cb432a490bb","mime_type":"application/pdf","arrived_at":"2019-02-06T23:04:00.933658Z","original_file_name":"test_invoice_1.pdf","content":"https://<example>.rossum.app/api/v1/documents/314621/content","metadata":{}},"updated_datapoints":[11213211,11213212]}
```

{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/781","settings":{"example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"password":"secret-importer-user-password"},"action":"updated","event":"annotation_content","annotation":{"document":"https://<example>.rossum.app/api/v1/documents/314621","id":314521,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/223","pages":["https://<example>.rossum.app/api/v1/pages/551518"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","previous_status":"importing","rir_poll_id":"54f6b91cfb751289e71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/314521","organization":"https://<example>.rossum.app/api/v1/organizations/1","content":[{"id":1123123,"url":"https://<example>.rossum.app/api/v1/annotations/314521/content/1123123","schema_id":"basic_info","category":"section","children":[{"id":20456864,"url":"https://<example>.rossum.app/api/v1/annotations/1/content/20456864","content":{"value":"18 492.48","normalized_value":"18492.48","page":2,...},"category":"datapoint","schema_id":"number","validation_sources":["checks","score"],"time_spent":0}]}],"time_spent":0,"metadata":{}},"document":{"id":314621,"url":"https://<example>.rossum.app/api/v1/documents/314621","s3_name":"272c2f41ae84a4f19a422cb432a490bb","mime_type":"application/pdf","arrived_at":"2019-02-06T23:04:00.933658Z","original_file_name":"test_invoice_1.pdf","content":"https://<example>.rossum.app/api/v1/documents/314621/content","metadata":{}},"updated_datapoints":[11213211,11213212]}
Example of a response forannotation_contenthook
annotation_content

```
{"messages":[{"content":"Invalid invoice number format","id":197467,"type":"error"}],"operations":[{"op":"replace","id":198143,"value":{"content":{"value":"John","position":[103,110,121,122],"page":1},"hidden":false,"options":[],"validation_sources":["human"]}},{"op":"remove","id":884061},{"op":"add","id":884060,"value":[{"schema_id":"item_description","content":{"page":1,"position":[162,852,371,875],"value":"Bottle"}}]}]}
```

{"messages":[{"content":"Invalid invoice number format","id":197467,"type":"error"}],"operations":[{"op":"replace","id":198143,"value":{"content":{"value":"John","position":[103,110,121,122],"page":1},"hidden":false,"options":[],"validation_sources":["human"]}},{"op":"remove","id":884061},{"op":"add","id":884060,"value":[{"schema_id":"item_description","content":{"page":1,"position":[162,852,371,875],"value":"Bottle"}}]}]}
Example data sent foremailevent to thehook.config.urlwhen email is received by Rossum mail server
email

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/781","settings":{"example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"password":"secret-importer-user-password"},"action":"received","event":"email","email":"https://<example>.rossum.app/api/v1/emails/987","queue":"https://<example>.rossum.app/api/v1/queues/41","files":[{"id":"1","filename":"image.png","mime_type":"image/png","n_pages":1,"height_px":100.0,"width_px":150.0,"document":"https://<example>.rossum.app/api/v1/documents/427"},{"id":"2","filename":"MS word.docx","mime_type":"application/vnd.openxmlformats-officedocument.wordprocessingml.document","n_pages":1,"height_px":null,"width_px":null,"document":"https://<example>.rossum.app/api/v1/documents/428"},{"id":"3","filename":"A4 pdf.pdf","mime_type":"application/pdf","n_pages":3,"height_px":3510.0,"width_px":2480.0,"document":"https://<example>.rossum.app/api/v1/documents/429"},{"id":"4","filename":"unknown_file","mime_type":"text/xml","n_pages":1,"height_px":null,"width_px":null,"document":"https://<example>.rossum.app/api/v1/documents/430"}],"headers":{"from":"test@example.com","to":"east-west-trading-co-a34f3a@<example>.rossum.app","reply-to":"support@example.com","subject":"Some subject","date":"Mon, 04 May 2020 11:01:32 +0200","message-id":"15909e7e68e4b5f56fd78a3b4263c4765df6cc4d","authentication-results":"example.com;\ndmarc=pass d=example.com"},"body":{"body_text_plain":"Some body","body_text_html":"<div dir=\"ltr\">Some body</div>"}}
```

{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/781","settings":{"example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"password":"secret-importer-user-password"},"action":"received","event":"email","email":"https://<example>.rossum.app/api/v1/emails/987","queue":"https://<example>.rossum.app/api/v1/queues/41","files":[{"id":"1","filename":"image.png","mime_type":"image/png","n_pages":1,"height_px":100.0,"width_px":150.0,"document":"https://<example>.rossum.app/api/v1/documents/427"},{"id":"2","filename":"MS word.docx","mime_type":"application/vnd.openxmlformats-officedocument.wordprocessingml.document","n_pages":1,"height_px":null,"width_px":null,"document":"https://<example>.rossum.app/api/v1/documents/428"},{"id":"3","filename":"A4 pdf.pdf","mime_type":"application/pdf","n_pages":3,"height_px":3510.0,"width_px":2480.0,"document":"https://<example>.rossum.app/api/v1/documents/429"},{"id":"4","filename":"unknown_file","mime_type":"text/xml","n_pages":1,"height_px":null,"width_px":null,"document":"https://<example>.rossum.app/api/v1/documents/430"}],"headers":{"from":"test@example.com","to":"east-west-trading-co-a34f3a@<example>.rossum.app","reply-to":"support@example.com","subject":"Some subject","date":"Mon, 04 May 2020 11:01:32 +0200","message-id":"15909e7e68e4b5f56fd78a3b4263c4765df6cc4d","authentication-results":"example.com;\ndmarc=pass d=example.com"},"body":{"body_text_plain":"Some body","body_text_html":"<div dir=\"ltr\">Some body</div>"}}
Example of a response foremailhook
email

```
{"files":[{"id":"3","values":[{"id":"email:invoice_id","value":"INV001234"},{"id":"email:customer_name","value":"John Doe"}]}],"additional_files":[{"document":"https://<example>.rossum.app/api/v1/documents/987","import_document":true,"values":[{"id":"email:internal_id","value":"0045654"}]}]}
```

{"files":[{"id":"3","values":[{"id":"email:invoice_id","value":"INV001234"},{"id":"email:customer_name","value":"John Doe"}]}],"additional_files":[{"document":"https://<example>.rossum.app/api/v1/documents/987","import_document":true,"values":[{"id":"email:internal_id","value":"0045654"}]}]}
Example data sent forinvocation.scheduledevent and action
invocation.scheduled

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/789","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"my-rossum-importer","password":"secret-importer-user-password"},"action":"scheduled","event":"invocation"}
```

{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/789","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"my-rossum-importer","password":"secret-importer-user-password"},"action":"scheduled","event":"invocation"}
Example data sent foruploadevent to thehook.config.urlwhen documents are uploaded (either through API or as an Email attachment)
upload

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/781","settings":{},"secrets":{},"action":"created","event":"upload","email":"https://<example>.rossum.app/api/v1/emails/987","upload":"https://<example>.rossum.app/api/v1/uploads/2046","metadata":{},"files":[{"document":"https://<example>.rossum.app/api/v1/documents/427","prevent_importing":false,"values":[],"queue":"https://<example>.rossum.app/api/v1/queues/41","annotation":null},{"document":"https://<example>.rossum.app/api/v1/documents/428","prevent_importing":true,"values":[],"queue":"https://<example>.rossum.app/api/v1/queues/41","annotation":"https://<example>.rossum.app/api/v1/annotations/1638"}],"documents":[{"id":427,"url":"https://<example>.rossum.app/api/v1/documents/427","mime_type":"application/pdf",...},{"id":428,"url":"https://<example>.rossum.app/api/v1/documents/428","mime_type":"application/json",...}]}
```

{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/781","settings":{},"secrets":{},"action":"created","event":"upload","email":"https://<example>.rossum.app/api/v1/emails/987","upload":"https://<example>.rossum.app/api/v1/uploads/2046","metadata":{},"files":[{"document":"https://<example>.rossum.app/api/v1/documents/427","prevent_importing":false,"values":[],"queue":"https://<example>.rossum.app/api/v1/queues/41","annotation":null},{"document":"https://<example>.rossum.app/api/v1/documents/428","prevent_importing":true,"values":[],"queue":"https://<example>.rossum.app/api/v1/queues/41","annotation":"https://<example>.rossum.app/api/v1/annotations/1638"}],"documents":[{"id":427,"url":"https://<example>.rossum.app/api/v1/documents/427","mime_type":"application/pdf",...},{"id":428,"url":"https://<example>.rossum.app/api/v1/documents/428","mime_type":"application/json",...}]}
Example of a response forupload.createdhook
upload.created

```
{"files":[{"document":"https://<example>.rossum.app/api/v1/documents/427","prevent_importing":false,"messages":[{"type":"error","content":"Some error message."}]},{"document":"https://<example>.rossum.app/api/v1/documents/428","prevent_importing":true},{"document":"https://<example>.rossum.app/api/v1/documents/429",},{"document":"https://<example>.rossum.app/api/v1/documents/430","messages":[{"type":"info","content":"Some info message."}]}]}
```

{"files":[{"document":"https://<example>.rossum.app/api/v1/documents/427","prevent_importing":false,"messages":[{"type":"error","content":"Some error message."}]},{"document":"https://<example>.rossum.app/api/v1/documents/428","prevent_importing":true},{"document":"https://<example>.rossum.app/api/v1/documents/429",},{"document":"https://<example>.rossum.app/api/v1/documents/430","messages":[{"type":"info","content":"Some info message."}]}]}
Webhook events specify when the hook should be notified. They can be defined as following:
- either as whole event containing all supported actions for its type (for exampleannotation_status)
annotation_status
- or as separately named actions for specified event (for exampleannotation_status.changed)
annotation_status.changed

#### Supported events and their actions

Event and ActionPayload (outside default attributes)ResponseDescriptionRetry on failureannotation_status.changedannotation, documentN/AAnnotationstatuschange occurredyesannotation_content.initializeannotation + content, document, updated_datapointsoperations, messagesAnnotation was initialized (data extracted)yesannotation_content.startedannotation + content, document, updated_datapoints (empty)operations, messagesUser entered validation screenno (interactive)annotation_content.user_updateannotation + content, document, updated_datapointsoperations, messages(Deprecated in favor ofannotation_content.updated) Annotation was updated by the userno (interactive)annotation_content.updatedannotation + content, document, updated_datapointsoperations, messagesAnnotation data was updated by the userno (interactive)annotation_content.confirmannotation + content, document, updated_datapoints (empty)operations, messagesUser confirmed validation screenno (interactive)annotation_content.exportannotation + content, document, updated_datapoints (empty)operations, messagesAnnotation is being moved to exported stateyesupload.createdfiles, documents, metadata, email, uploadfilesUpload object was createdyesemail.receivedfiles, headers, body, email, queuefiles (*)Email with attachments was receivedyesinvocation.scheduledN/AN/AHook was invoked at the scheduled timeyesinvocation.manualcustom payload fieldsforwarded hook responseEvent formanual hook triggeringno
annotation_status.changed
status
annotation_content.initialize
annotation_content.started
annotation_content.user_update
annotation_content.updated
annotation_content.updated
annotation_content.confirm
annotation_content.export
upload.created
email.received
invocation.scheduled
invocation.manual
(*) May also contain other optional attributes - read more inthis section.
annotation_content.started
annotation_content.updated
annotation_content.user_update
/validate
- Whenannotation_content.exportaction fails, annotation is switched to thefailed_exportstate.
annotation_content.export
failed_export
- Whenresponse from webhookonannotation_content.exportcontains a message of typeerror, the annotation is switched to thefailed_exportstate.
annotation_content.export
error
failed_export
- Theupdated_datapointslist is never empty forannotation_content.updatedonly triggered by interactive date changes actions.
updated_datapoints
annotation_content.updated
- Theupdated_datapointslist is always empty for theannotation_content.exportaction.
updated_datapoints
annotation_content.export
- Theupdated_datapointslist is empty for theannotation_content.initializeaction ifrun_after=[], but it can have data from its predecessor if chained viarun_after.
updated_datapoints
annotation_content.initialize
run_after=[]
run_after
- Theupdated_datapointslist may also be empty forannotation_content.user_updatein case of an action triggered interactively by a user, but with no data changes (e.g. after opening validation screen or eventually at its confirmation issued by the Rossum UI).
updated_datapoints
annotation_content.user_update
- For each webhook call there is a 30 seconds timeout by default (this applies to all events and actions).
It can be modified inconfigwith attributetimeout_s(min=0, max=60, only for non-interactive webhooks).
config
timeout_s
- In case a non-interactive webhook call fails (check the configuration ofretry_on_any_non_2xxattribute
of thewebhookto see what statuses this includes), it is retried within 30 seconds by default.
There are up to 5 attempts performed. This number can be modified inconfigwith attributeretry_count(min=0, max=4, only for non-interactive webhooks).
retry_on_any_non_2xx
config
retry_count
timeout_s
config
Non-interactive webhooks can use also asynchronous framework:
- Webhook returns an HTTP status 202 and url for polling in the responseLocationheader.
Location
- The provided polling url is polled every 30 seconds until a response with 201 status code is received. The response
body is then taken as the hook call result.
- The polling continues until 201 response is received or until the maximum polling time is exceeded. See
themax_polling_time_sattribute of thehook.configfor more details.
max_polling_time_s
- In case the polling request returns one of the following status codes:408, 429, 500, 502, 503, 504, it is retried
and the polling continues. (This is not considered a polling failure.)
408, 429, 500, 502, 503, 504
- In case the polling request fails (returns any error status code other than408, 429, 500, 502, 503, 504or exceeds
the maximum polling time), the original webhook call is retried (by default). The number of retry attempts is set by
theretry_countattribute of thehook.config.
408, 429, 500, 502, 503, 504
retry_count
- Retries after polling can be enabled/disabled by theretry_after_polling_failureattribute of thehook.config.
retry_after_polling_failure
To show an overview of the Hook events and when they are happening, this diagram was created.

#### Hooks common attributes

KeyTypeDescriptionrequest_idUUIDHookcall request IDtimestampdatetimeTimestamp when thehookwas calledhookURLHook's urlactionstringHook'sactioneventstringHook'seventsettingsobjectCopy ofhook.settingsattribute

#### Annotation status event data format

annotation_statusevent contains following additional event specific attributes.
annotation_status
KeyTypeDescriptionannotationobjectAnnotation object (enriched with attributeprevious_status)documentobjectDocument object (attributeannotationsis excluded)queues*list[object]list of relatedqueueobjectsmodifiers*list[object]list of relatedmodifierobjectsschemas*list[object]list of relatedschemaobjectsemails*list[object]list of relatedemailobjects (for annotations created after email ingestion)related_emails*list[object]list of relatedemailsobjects (other related emails)relations*list[object]list of relatedrelationobjectschild_relations*list[object]list of relatedchild_relationobjectssuggested_edits*list[object]list of relatedsuggested_editsobjectsassignees*list[object]list of relatedassigneeobjectspages*list[object]list of relatedpagesobjectsnotes*list[object]list of relatednotesobjectslabels*list[object]list of relatedlabelsobjectsautomation_blockers*list[object]list of relatedautomation_blockersobjects
previous_status
annotations
*Attribute is only included in the request when specified inhook.sideload. Please note that sideloading of modifier object from different organization is not supported and that sideloading can decrease performance. See alsoannotationsideloading section.
hook.sideload
Example data sent to hook with sideloadedqueueobjects

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","hook":"https://<example>.rossum.app/api/v1/hooks/781","action":"changed","event":"annotation_status",...,"queues":[{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198",...,"metadata":{},"use_confirmed_state":false,"settings":{}}]}
```

{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","hook":"https://<example>.rossum.app/api/v1/hooks/781","action":"changed","event":"annotation_status",...,"queues":[{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198",...,"metadata":{},"use_confirmed_state":false,"settings":{}}]}

#### Annotation content event data format

annotation_contentevent contains following additional event specific attributes.
annotation_content
KeyTypeDescriptionannotationobjectAnnotation object. Content is pre-loaded withannotation data. Annotation data are enriched withnormalized_value, see example.documentobjectDocument object (attributeannotationsis excluded)updated_datapoints**list[int]List of IDs of datapoints that were changed by last or all predecessor events.queues*list[object]list of relatedqueueobjectsmodifiers*list[object]list of relatedmodifierobjectsschemas*list[object]list of relatedschemaobjectsemails*list[object]list of relatedemailobjects (for annotations created after email ingestion)related_emails*list[object]list of relatedemailsobjects (other related emails)relations*list[object]list of relatedrelationobjectschild_relations*list[object]list of relatedchild_relationobjectssuggested_edits*list[object]list of relatedsuggested_editsobjectsassignees*list[object]list of relatedassigneeobjectspages*list[object]list of relatedpagesobjectsnotes*list[object]list of relatednotesobjectslabels*list[object]list of relatedlabelsobjectsautomation_blockers*list[object]list of relatedautomation_blockersobjects
normalized_value
annotations
*Attribute is only included in the request when specified inhook.sideload. Please note that sideloading of modifier object from different organization is not supported and that sideloading can decrease performance. See alsoannotationsideloading section.
hook.sideload
**If therun_afterattribute chains the hooks, the updated_datapoints will contain a list of all datapoint ids that were updated by any of the predecessive hooks. Moreover, in case ofaddoperation on a multivalue table, theupdated_datapointswill contain theidof the multivalue, theidof the new tuple datapoints and theidof all the newly created cell datapoints.
run_after
add
updated_datapoints
id
id
id

#### Annotation content event response format

All of theannotation_contentevents expect a JSON object with the following
optional lists in the response:messagesandoperations
annotation_content
messages
operations
Themessageobject contains attributes:
message
KeyTypeDescriptionidintegerOptional unique id of the relevant datapoint; omit for a document-wide issuestypeenumOne of:error,warningorinfo.contentstringA descriptive message to be shown to the userdetailobjectDetail object that enhances the response from a hook. (For more info refer tomessage detail)
For example, you may useerrorfor fatals like a missing required field,
whereasinfois suitable to decorate a supplier company id with its name as
looked up in the supplier's database.
Theoperationsobject describes operation to be performed on the annotation
data (replace,add,remove). Format of theoperationskey is the same as for
bulk update of annotations, please refer to theannotation
dataAPI for complete description.
operations
operations
It's possible to use the same format even with non-2XX response codes. In this type of response,operationsare not considered.
operations
Example of a parsable error response

```
{"messages":[{"id":"all","type":"error","content":"custom error message to be displayed in the UI"}]}
```

{"messages":[{"id":"all","type":"error","content":"custom error message to be displayed in the UI"}]}
initializeevent ofannotation_contentaction additionally accepts list ofautomation_blockersobjects.
This allows for manual creation ofautomation blockersoftypeextensionand therefore stops theautomationwithout the need to create an error message.
initialize
annotation_content
automation_blockers
extension
Theautomation_blockersobject contains attributes
automation_blockers
KeyTypeDescriptionidintegerOptional unique id of the relevant datapoint; omit for a document-wide issuescontentstrA descriptive message to be stored as anautomation blocker
Example of a response forannotation_content.initializehook creating automation blockers
annotation_content.initialize

```
{"messages":[...],"operations":[...],"automation_blockers":[{"id":1357,"content":"Unregistered vendor"},{"content":"PO not found in the master data!"}]}
```

{"messages":[...],"operations":[...],"automation_blockers":[{"id":1357,"content":"Unregistered vendor"},{"content":"PO not found in the master data!"}]}

#### Email received event data format

emailevent contains following additional event specific attributes.
email
KeyTypeDescriptionfileslist[object]List of objects with metadata of each attachment contained in the arriving email.headersobjectHeaders extracted from the arriving email.bodyobjectBody extracted from the arriving email.emailURLURL of the arriving email.queueURLURL of the arriving email's queue.
Thefilesobject contains attributes:
files
KeyTypeDescriptionidstringSome arbitrary identifier.filenamestringName of the attachment.mime_typestringMIME typeof the attachment.n_pagesintegerNumber of pages (defaults to 1 if it could not be acquired).height_pxfloatHeight in pixels (300 DPI is assumed for PDF files, defaults tonullif it could not be acquired).width_pxfloatWidth in pixels (300 DPI is assumed for PDF files, defaults tonullif it could not be acquired).documentURLURL of related document object.
null
null
Theheadersobject contains the same values as are available forinitialization of valuesinemail_header:<id>(namely:from,to,reply-to,subject,message-id,date).
headers
email_header:<id>
from
to
reply-to
subject
message-id
date
Thebodyobject contains thebody_text_plainandbody_text_html.
body
body_text_plain
body_text_html

#### Email received event response format

All of theemailevents expect a JSON object with the following lists in the response:files,additional_files,extracted_original_sender
email
files
additional_files
extracted_original_sender
Thefilesobject contains attributes:
files
KeyTypeDescriptionidintidof file that will be used for creating anannotationvalueslist[object]This is used to initialize datapoint values. Seevaluesobject description below
id
annotation
values
Thevaluesobject consists of the following:
values
KeyTypeDescriptionidstringId of value - must start withemail:prefix (to use this value refer to it inrir_field_namesfield in the schema similarly as describedhere).valuestringString value to be used when annotation content is being constructed
email:
rir_field_names
This is useful for filtering out unwanted files by some measures that are not available in Rossum by default.
files
values
Theadditional_filesobject contains attributes:
additional_files
KeyTypeDefaultRequiredDescriptiondocumentURLyesURL of the document object that should be included. If document belongs to an annotation it must also belong to the same queue as email inbox.valueslist[object][]noThis is used to initialize datapoint values. Seevaluesobject description aboveimport_documentboolfalsenoSet totrueif Rossum should import document and create an annotation for it, otherwise it will be just linked as an email attachment. Only applicable if document hasn't already an annotation attached.
[]
values
false
true
Theextracted_original_senderobject looks as follows:
extracted_original_sender
KeyTypeDescriptionextracted_original_senderemail_address_objectInformation about sender containing keysemailandname.
email
name
This is useful for updating the email address field on email object with a new sender name and email address.
extracted_original_sender

#### Upload created event data format

uploadevent contains following additional event specific attributes.
upload
KeyTypeDescriptionfileslist[object]List of objects with metadata of each uploaded document.documentslist[object]List of document objects corresponding with the files object.uploadobjectObject representing the upload.metadataobjectClient data passed in through the upload resource to create annotations with.emailURLURL of the arriving email ornullif the document was uploaded via API.
null
Thefilesobject contains attributes:
files
KeyTypeDescriptiondocumentURLURL of the uploaded document object.prevent_importingboolIf set no annotation is going to be created for the document or if already existing it is not going to be switched toimportingstatus.valueslist[object]This is used to initialize datapoint values. Seevaluesobject description belowqueueURLURL of the queue the document is being uploaded to.annotationURLURL of the documents annotation ornullif it doesn't exist.
importing
values
null
Thevaluesobject consists of the following:
values
KeyTypeDescriptionidstringId of value (to use this value refer to it inrir_field_namesfield in the schema similarly as describedhere).valuestringString value to be used when annotation content is being constructed
rir_field_names

#### Upload created event response format

All of theuploadevents expect a JSON object with thefilesobject list in the response.
upload
files
Thefilesobject contains attributes:
files
KeyTypeDescriptionRequireddocumentURLURL of the uploaded document object.trueprevent_importingboolIf set no annotation is going to be created for the document or if already exists it is not going to be switched toimportingstatus. Optional, default false.falsemessageslist[object]List ofmessagesthat will be appended to the related annotation.false
importing

### Validating payloads from Rossum

Example of hook receiver, which verifies the validity of Rossum request

```
importhashlibimporthmacfromflaskimportFlask,request,abortapp=Flask(__name__)SECRET_KEY="<Your secret key stored in hook.config.secret>"# never store this in code@app.route("/test_hook",methods=["POST"])deftest_hook():digest=hmac.new(SECRET_KEY.encode(),request.data,hashlib.sha256).hexdigest()try:prefix,signature=request.headers["X-Rossum-Signature-SHA256"].split("=")exceptValueError:abort(401,"Incorrect header format")ifnot(prefix=="sha256"andhmac.compare_digest(signature,digest)):abort(401,"Authorization failed.")return
```

importhashlibimporthmacfromflaskimportFlask,request,abortapp=Flask(__name__)SECRET_KEY="<Your secret key stored in hook.config.secret>"# never store this in code@app.route("/test_hook",methods=["POST"])deftest_hook():digest=hmac.new(SECRET_KEY.encode(),request.data,hashlib.sha256).hexdigest()try:prefix,signature=request.headers["X-Rossum-Signature-SHA256"].split("=")exceptValueError:abort(401,"Incorrect header format")ifnot(prefix=="sha256"andhmac.compare_digest(signature,digest)):abort(401,"Authorization failed.")return
For authorization of payloads, theshared secretmethod is used.
When a secret token is set inhook.config.secret, Rossum uses it to create a hash signature with each payload.
This hash signature is passed along with each request in the headers asX-Rossum-Signature-SHA256.
hook.config.secret
X-Rossum-Signature-SHA256
The goal is to compute a hash usinghook.config.secretand the request body,
and ensure that the signature produced by Rossum is the same. Rossum uses HMAC SHA256 signature by default.
hook.config.secret
Previously, Rossum was using SHA1 algorithm to sign the payload. This option is
still available as a legacyX-Elis-Signatureheader. Please contact
Rossum support to enable this header in case it is missing.
X-Elis-Signature
Webhook requests may also be authenticated using a client SSL certificate, seeHookAPI for reference.

### Access to Rossum API

You can access Rossum API from the Webhook. Each execution gets unique API key. The key is valid
for 10 minutes or until Rossum receives a response from the Webhook. You can settoken_lifetime_sup to 2 hours to keep
the token valid longer. The API key and the environment's base URL are passed to webhooks as a first-level attributesrossum_authorization_tokenandbase_urlwithin the webhook payload.
token_lifetime_s
rossum_authorization_token
base_url


## Serverless Function Extension

Serverless functions allow to extend Rossum functionality without setup and
maintenance of additional services.
Webhooksand Serverless functions share a basic setup: input and output data
format and error handling. They are both configured using ahookAPI
object.
Unlike webhooks, serverless functions do not send the event and action
notifications to a specific URL. Instead, the function'scodesnippet is
executed within the Rossum platform. SeefunctionAPI
description for details about how to set up a serverless function and connect it
to the queue.

### Supported events and their actions

For description of supported events, actions and input/output data examples,
please refer toWebhook Extensionssection.

### Supported runtimes

Currently, Rossum supportsNodeJSandPythonto execute serverless
functions. See the table below for a full list of supported runtimes. If you would like to use another runtime,
please let us know at product@rossum.ai.
Please be aware that we may eventually deprecate and remove runtimes in the future.
NameIdentifierDeprecation dateBlock function creation dateRemoval dateNotePython 3.12python3.12not schedulednot schedulednot scheduledNodeJS 22nodejs22.xnot schedulednot schedulednot scheduled
python3.12
nodejs22.x

#### Runtime deprecations

We schedule runtime deprecation when it is being phased out by the serverless vendors. The recommended action
is to upgrade to one of the up-to-date runtimes.
See the table above for specific deprecation dates of individual runtimes.
- Deprecation date- Date when the deprecation is announced.
- Block function creation date- From this date, it will not be possible to create new extensions with the
deprecated runtime. Existing extensions can be used as they are and their code can be updated until the removal date.
- Removal date- All extensions will be automatically switched to the up-to-date runtime on this date.
We recommend making the switch earlier to test and update the code if needed, to avoid any issues.

#### Python Runtime and Rossum Transaction Scripts

Thepython3.12runtime includes atxscriptmodule that providesconvenience
functionalityfor working with Rossum objects,
in particular in the context of theannotation_contentevent.
python3.12
txscript
annotation_content

### Implementation

Example serverless function usable forannotation_contentevent (Python implementation).
annotation_content

```
'''
This custom serverless function example demonstrates showing messages to the
user on the validation screen, updating values of specific fields, and
executing actions on the annotation.

See https://elis.rossum.ai/api/docs/#rossum-transaction-scripts for more examples.
'''fromtxscriptimportTxScript,default_to,substitutedefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)forrowint.field.line_items:ifdefault_to(row.item_amount_base,0)>=1000000:t.show_warning('Value is too big',row.item_amount_base)# Remove dashes from document_id# Note: This type of operation is strongly discouraged in serverless# functions, since the modification is non-transparent to the user and# it is hard to trace down which hook modified the field.# Always prefer making a formula field!t.field.document_id=substitute(r'-','',t.field.document_id)ifdefault_to(t.field.amount_total,0)>1000000:print("postponing")t.annotation.action("postpone")returnt.hook_response()returnt.hook_response()
```

'''
This custom serverless function example demonstrates showing messages to the
user on the validation screen, updating values of specific fields, and
executing actions on the annotation.

See https://elis.rossum.ai/api/docs/#rossum-transaction-scripts for more examples.
'''fromtxscriptimportTxScript,default_to,substitutedefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)forrowint.field.line_items:ifdefault_to(row.item_amount_base,0)>=1000000:t.show_warning('Value is too big',row.item_amount_base)# Remove dashes from document_id# Note: This type of operation is strongly discouraged in serverless# functions, since the modification is non-transparent to the user and# it is hard to trace down which hook modified the field.# Always prefer making a formula field!t.field.document_id=substitute(r'-','',t.field.document_id)ifdefault_to(t.field.amount_total,0)>1000000:print("postponing")t.annotation.action("postpone")returnt.hook_response()returnt.hook_response()
Example serverless function usable forannotation_contentevent (JavaScript/NodeJS implementation).
annotation_content

```
// This serverless function example can be used for annotation_content events// (e.g. updated action). annotation_content events provide annotation// content tree as the input.//// The function below shows how to:// 1. Display a warning message to the user if "item_amount_base" field of//    a line item exceeds a predefined threshold// 2. Removes all dashes from the "invoice_id" field//// item_amount_base and invoice_id should be fields defined in a schema.// --- ROSSUM HOOK REQUEST HANDLER ---// The rossum_hook_request_handler is an mandatory main function that accepts// input and produces output of the rossum serverless function hook.// @param {Object} payload - see https://example.rossum.app/api/docs/#annotation-content-event-data-format// @returns {Object} - the messages and operations that update the annotation contentexports.rossum_hook_request_handler=async(payload)=>{constcontent=payload.annotation.content;try{// Values over the threshold trigger a warning messageconstTOO_BIG_THRESHOLD=1000000;// List of all datapoints of item_amount_base schema idconstamountBaseColumnDatapoints=findBySchemaId(content,'item_amount_base',);constmessages=[];for(vari=0;i<amountBaseColumnDatapoints.length;i++){// Use normalized_value for comparing values of Date and Number fields (https://example.rossum.app/api/docs/#content-object)if(amountBaseColumnDatapoints[i].content.normalized_value>=TOO_BIG_THRESHOLD){messages.push(createMessage('warning','Value is too big',amountBaseColumnDatapoints[i].id,),);}}// There should be only one datapoint of invoice_id schema idconst[invoiceIdDatapoint]=findBySchemaId(content,'invoice_id');// "Replace" operation is returned to update the invoice_id valueconstoperations=[createReplaceOperation(invoiceIdDatapoint,invoiceIdDatapoint.content.value.replace(/-/g,''),),];// Return messages and operations to be used to update current annotation datareturn{messages,operations,};}catch(e){// In case of exception, create and return error message. This may be useful for debugging.constmessages=[createMessage('error','Serverless Function:'+e.message)];return{messages,};}};// --- HELPER FUNCTIONS ---// Return datapoints matching a schema id.// @param {Object} content - the annotation content tree (see https://example.rossum.app/api/docs/#annotation-data)// @param {string} schemaId - the field's ID as defined in the extraction schema(see https://example.rossum.app/api/docs/#document-schema)// @returns {Array} - the list of datapoints matching the schema IDconstfindBySchemaId=(content,schemaId)=>content.reduce((results,dp)=>dp.schema_id===schemaId?[...results,dp]:dp.children?[...results,...findBySchemaId(dp.children,schemaId)]:results,[],);// Create a message which will be shown to the user// @param {number} datapointId - the id of the datapoint where the message will appear (null for "global" messages).// @param {String} messageType - the type of the message, any of {info|warning|error}. Errors prevent confirmation in the UI.// @param {String} messageContent - the message shown to the user// @returns {Object} - the JSON message definition (see https://example.rossum.app/api/docs/#annotation-content-event-response-format)constcreateMessage=(type,content,datapointId=null)=>({content:content,type:type,id:datapointId,});// Replace the value of the datapoint with a new value.// @param {Object} datapoint - the content of the datapoint// @param {string} - the new value of the datapoint// @return {Object} - the JSON replace operation definition (see https://example.rossum.app/api/docs/#annotation-content-event-response-format)constcreateReplaceOperation=(datapoint,newValue)=>({op:'replace',id:datapoint.id,value:{content:{value:newValue,},},});
```

// This serverless function example can be used for annotation_content events// (e.g. updated action). annotation_content events provide annotation// content tree as the input.//// The function below shows how to:// 1. Display a warning message to the user if "item_amount_base" field of//    a line item exceeds a predefined threshold// 2. Removes all dashes from the "invoice_id" field//// item_amount_base and invoice_id should be fields defined in a schema.// --- ROSSUM HOOK REQUEST HANDLER ---// The rossum_hook_request_handler is an mandatory main function that accepts// input and produces output of the rossum serverless function hook.// @param {Object} payload - see https://example.rossum.app/api/docs/#annotation-content-event-data-format// @returns {Object} - the messages and operations that update the annotation contentexports.rossum_hook_request_handler=async(payload)=>{constcontent=payload.annotation.content;try{// Values over the threshold trigger a warning messageconstTOO_BIG_THRESHOLD=1000000;// List of all datapoints of item_amount_base schema idconstamountBaseColumnDatapoints=findBySchemaId(content,'item_amount_base',);constmessages=[];for(vari=0;i<amountBaseColumnDatapoints.length;i++){// Use normalized_value for comparing values of Date and Number fields (https://example.rossum.app/api/docs/#content-object)if(amountBaseColumnDatapoints[i].content.normalized_value>=TOO_BIG_THRESHOLD){messages.push(createMessage('warning','Value is too big',amountBaseColumnDatapoints[i].id,),);}}// There should be only one datapoint of invoice_id schema idconst[invoiceIdDatapoint]=findBySchemaId(content,'invoice_id');// "Replace" operation is returned to update the invoice_id valueconstoperations=[createReplaceOperation(invoiceIdDatapoint,invoiceIdDatapoint.content.value.replace(/-/g,''),),];// Return messages and operations to be used to update current annotation datareturn{messages,operations,};}catch(e){// In case of exception, create and return error message. This may be useful for debugging.constmessages=[createMessage('error','Serverless Function:'+e.message)];return{messages,};}};// --- HELPER FUNCTIONS ---// Return datapoints matching a schema id.// @param {Object} content - the annotation content tree (see https://example.rossum.app/api/docs/#annotation-data)// @param {string} schemaId - the field's ID as defined in the extraction schema(see https://example.rossum.app/api/docs/#document-schema)// @returns {Array} - the list of datapoints matching the schema IDconstfindBySchemaId=(content,schemaId)=>content.reduce((results,dp)=>dp.schema_id===schemaId?[...results,dp]:dp.children?[...results,...findBySchemaId(dp.children,schemaId)]:results,[],);// Create a message which will be shown to the user// @param {number} datapointId - the id of the datapoint where the message will appear (null for "global" messages).// @param {String} messageType - the type of the message, any of {info|warning|error}. Errors prevent confirmation in the UI.// @param {String} messageContent - the message shown to the user// @returns {Object} - the JSON message definition (see https://example.rossum.app/api/docs/#annotation-content-event-response-format)constcreateMessage=(type,content,datapointId=null)=>({content:content,type:type,id:datapointId,});// Replace the value of the datapoint with a new value.// @param {Object} datapoint - the content of the datapoint// @param {string} - the new value of the datapoint// @return {Object} - the JSON replace operation definition (see https://example.rossum.app/api/docs/#annotation-content-event-response-format)constcreateReplaceOperation=(datapoint,newValue)=>({op:'replace',id:datapoint.id,value:{content:{value:newValue,},},});
To implement a serverless function, create ahookobject of typefunction. Usecodeobject config attribute to specify a serialized source
code. You can use a code editor built-in to the Rossum UI, which also allows to
test and debug the function before updating the code of the function itself.
function
code
See Python and NodeJS examples of a serverless function implementation next to this section
or check outthis article(and
others in the relevant section).
If there is an issue with an extension code itself, it will be displayed asCallFunctionExceptionin the
annotation view. Raising this exception usually means issues such as:
CallFunctionException
- undefined variables are called in the code
- the code is raising an exception as a response rather than returning a proper response

### Testing

To write, test and debug a serverless function, you can refer tothis guide.

### Limitations

By default, no internet access is allowed from a serverless function, except
the Rossum API. If your functions require internet access to work properly,
e.g. when exporting data over API to ERP system, please let us know at
product@rossum.ai.

### Access Rossum API

The access to the Rossum API is granted through a proxy server,HTTPS_PROXYenvironment variable should be used to get its URL. See examples
below to see how to access Rossum API from a serverless function. Python'surllib.requestcan handle HTTPS proxy from environment variable on its own.
For Node.js thehttps.globalAgentis set to anhttps-proxy-agentinstance
if present in the selected library pack.
HTTPS_PROXY
urllib.request
https.globalAgent
https-proxy-agent
Python code snippet to access Rossum API to get a list of queue names

```
importjsonimporturllib.requestdefrossum_hook_request_handler(payload):request=urllib.request.Request("https://<example>.rossum.app/api/v1/queues",headers={"Authorization":"Bearer "+payload["rossum_authorization_token"]})withurllib.request.urlopen(request)asresponse:queues=json.loads(response.read())queue_names=(q["name"]forqinqueues["results"])return{"messages":[{"type":"info","content":", ".join(queue_names)}]}
```

importjsonimporturllib.requestdefrossum_hook_request_handler(payload):request=urllib.request.Request("https://<example>.rossum.app/api/v1/queues",headers={"Authorization":"Bearer "+payload["rossum_authorization_token"]})withurllib.request.urlopen(request)asresponse:queues=json.loads(response.read())queue_names=(q["name"]forqinqueues["results"])return{"messages":[{"type":"info","content":", ".join(queue_names)}]}
NodeJS code snippet to access Rossum API to get a list of queue names

```
exports.rossum_hook_request_handler=async(payload)=>{consttoken=payload.rossum_authorization_token;queues=JSON.parse(awaitgetFromRossumApi("https://<example>.rossum.app/api/v1/queues",token));queue_names=queues.results.map(q=>q.name).join(",")return{"messages":[{"type":"info","content":queue_names}]};}constgetFromRossumApi=async(url,token)=>{varhttp=require('http');constproxy=newURL(process.env.HTTPS_PROXY);constoptions={hostname:proxy.hostname,port:proxy.port,path:url,method:'GET',headers:{'Authorization':'token'+token,},};constresponse=awaitnewPromise((resolve,reject)=>{letdataString='';constreq=http.request(options,function(res){res.on('data',chunk=>{dataString+=chunk;});res.on('end',()=>{resolve({statusCode:200,body:dataString});});});req.on('error',(e)=>{reject({statusCode:500,body:'Something went wrong!'});});req.end()});returnresponse.body}
```

exports.rossum_hook_request_handler=async(payload)=>{consttoken=payload.rossum_authorization_token;queues=JSON.parse(awaitgetFromRossumApi("https://<example>.rossum.app/api/v1/queues",token));queue_names=queues.results.map(q=>q.name).join(",")return{"messages":[{"type":"info","content":queue_names}]};}constgetFromRossumApi=async(url,token)=>{varhttp=require('http');constproxy=newURL(process.env.HTTPS_PROXY);constoptions={hostname:proxy.hostname,port:proxy.port,path:url,method:'GET',headers:{'Authorization':'token'+token,},};constresponse=awaitnewPromise((resolve,reject)=>{letdataString='';constreq=http.request(options,function(res){res.on('data',chunk=>{dataString+=chunk;});res.on('end',()=>{resolve({statusCode:200,body:dataString});});});req.on('error',(e)=>{reject({statusCode:500,body:'Something went wrong!'});});req.end()});returnresponse.body}


## Connector Extension

The connector component is aimed at two main use-cases: applying custom business rules
during data validation, and direct integration of Rossum with downstream systems.
The connector component receives two types of callbacks - an on-the-fly validation
callback on every update of captured data, and an on-export save callback when the
document capture is finalized.
The custom business rules take use chiefly of the on-the-fly validation callback.
The connector can auto-validate and transform both the initial AI-based extractions
and each user operator edit within the validation screen; based on the input, it can
push user-visible messages and value updates back to Rossum. This allows for both simple
tweaks (like verifying that two amounts sum together or transforming decimal points
to thousand separators) and complex functionality like intelligent PO match.
The integration with downstream systems on the other hand relies mainly on the save
callback.  At the same moment a document is exported from Rossum, it can be imported
to a downstream system.  Since there are typically constraints on the captured data,
these constraints can be enforced even within the validation callback.

### Implement a connector

Connectors are designed to be implemented using a push-model using common HTTPS
protocol. When annotation data is changed, or when data export is triggered,
specific connector endpoint is called with annotation data as a request payload.
The connector must be deployed with a public IP address so that the Rossum platform
can call its endpoints; for testing, a middleware likengrokorserveomay come useful.
Example of a valid no-op (empty)validateresponse
validate

```
{"messages":[],"updated_datapoints":[]}
```

{"messages":[],"updated_datapoints":[]}
Example of a valid no-op (empty)saveresponse
save

```
{}
```

{}
The connector API consists of two endpoints,validateandsave,
described below.
A connector must always implement both endpoints (though they may not necessarily
perform a function in a particular connector - see the right column for an empty
reply example), the platform raises an error if it is not able to run an endpoint.
- run on HTTPS and have a valid public certificatebe fast enough to keep up the pace with Rossum interactive behaviorbe able to receive traffic from any IP address. (Source IP address may change over time.)require authentication by authentication token to prevent data leaks or forgery
- be fast enough to keep up the pace with Rossum interactive behaviorbe able to receive traffic from any IP address. (Source IP address may change over time.)require authentication by authentication token to prevent data leaks or forgery
- be able to receive traffic from any IP address. (Source IP address may change over time.)require authentication by authentication token to prevent data leaks or forgery
- require authentication by authentication token to prevent data leaks or forgery

### Setup a connector

The next step after implementing the first version of a connector is configuring it
in the Rossum platform.
In Rossum, aconnector objectdefinesservice_urlandparamsfor
construction of HTTPS requests andauthorization_tokenthat is passed in
every request to authenticate the caller as the actual Rossum server. It may also
uniquely identify the organization when multiple Rossum organizations share the
same connector server.
service_url
params
authorization_token
To set up a connector for aqueue, create aconnector objectusing either our API or
therossumtool
–follow these instructions.
A connector object may be associated with one or more queues. One queue can only have one connector object associated with it.

### Connector API

Example data sent to connector (validate,save)
validate
save

```
{"meta":{"document_url":"https://<example>.rossum.app/api/v1/documents/6780","arrived_at":"2019-01-30T07:55:13.208304Z","original_file":"https://<example>.rossum.app/api/v1/original/bf0db41937df8525aa7f3f9b18a562f3","original_filename":"Invoice.pdf","queue_name":"Invoices","workspace_name":"EU","organization_name":"East West Trading Co","annotation":"https://<example>.rossum.app/api/v1/annotations/4710","queue":"https://<example>.rossum.app/api/v1/queues/63","workspace":"https://<example>.rossum.app/api/v1/workspaces/62","organization":"https://<example>.rossum.app/api/v1/organizations/1","modifier":"https://<example>.rossum.app/api/v1/users/27","updated_datapoint_ids":["197468"],"modifier_metadata":{},"queue_metadata":{},"annotation_metadata":{},"rir_poll_id":"54f6b9ecfa751789f71ddf12","automated":false},"content":[{"id":"197466","category":"section","schema_id":"invoice_info_section","children":[{"id":"197467","category":"datapoint","schema_id":"invoice_number","page":1,"position":[916,168,1190,222],"rir_position":[916,168,1190,222],"rir_confidence":0.97657,"value":"FV103828806S","validation_sources":["score"],"type":"string"},{"id":"197468","category":"datapoint","schema_id":"date_due","page":1,"position":[938,618,1000,654],"rir_position":[940,618,1020,655],"rir_confidence":0.98279,"value":"12/22/2018","validation_sources":["score"],"type":"date"},{"id":"197469","category":"datapoint","schema_id":"amount_due","page":1,"position":[1134,1050,1190,1080],"rir_position":[1134,1050,1190,1080],"rir_confidence":0.74237,"value":"55.20","validation_sources":["human"],"type":"number"}]},{"id":"197500","category":"section","schema_id":"line_items_section","children":[{"id":"197501","category":"multivalue","schema_id":"line_items","children":[{"id":"198139","category":"tuple","schema_id":"line_item","children":[{"id":"198140","category":"datapoint","schema_id":"item_desc","page":1,"position":[173,883,395,904],"rir_position":null,"rir_confidence":null,"value":"Red Rose","validation_sources":[],"type":"string"},{"id":"198142","category":"datapoint","schema_id":"item_net_unit_price","page":1,"position":[714,846,768,870],"rir_position":null,"rir_confidence":null,"value":"1532.02","validation_sources":["human"],"type":"number"}]}]}]}]}
```

{"meta":{"document_url":"https://<example>.rossum.app/api/v1/documents/6780","arrived_at":"2019-01-30T07:55:13.208304Z","original_file":"https://<example>.rossum.app/api/v1/original/bf0db41937df8525aa7f3f9b18a562f3","original_filename":"Invoice.pdf","queue_name":"Invoices","workspace_name":"EU","organization_name":"East West Trading Co","annotation":"https://<example>.rossum.app/api/v1/annotations/4710","queue":"https://<example>.rossum.app/api/v1/queues/63","workspace":"https://<example>.rossum.app/api/v1/workspaces/62","organization":"https://<example>.rossum.app/api/v1/organizations/1","modifier":"https://<example>.rossum.app/api/v1/users/27","updated_datapoint_ids":["197468"],"modifier_metadata":{},"queue_metadata":{},"annotation_metadata":{},"rir_poll_id":"54f6b9ecfa751789f71ddf12","automated":false},"content":[{"id":"197466","category":"section","schema_id":"invoice_info_section","children":[{"id":"197467","category":"datapoint","schema_id":"invoice_number","page":1,"position":[916,168,1190,222],"rir_position":[916,168,1190,222],"rir_confidence":0.97657,"value":"FV103828806S","validation_sources":["score"],"type":"string"},{"id":"197468","category":"datapoint","schema_id":"date_due","page":1,"position":[938,618,1000,654],"rir_position":[940,618,1020,655],"rir_confidence":0.98279,"value":"12/22/2018","validation_sources":["score"],"type":"date"},{"id":"197469","category":"datapoint","schema_id":"amount_due","page":1,"position":[1134,1050,1190,1080],"rir_position":[1134,1050,1190,1080],"rir_confidence":0.74237,"value":"55.20","validation_sources":["human"],"type":"number"}]},{"id":"197500","category":"section","schema_id":"line_items_section","children":[{"id":"197501","category":"multivalue","schema_id":"line_items","children":[{"id":"198139","category":"tuple","schema_id":"line_item","children":[{"id":"198140","category":"datapoint","schema_id":"item_desc","page":1,"position":[173,883,395,904],"rir_position":null,"rir_confidence":null,"value":"Red Rose","validation_sources":[],"type":"string"},{"id":"198142","category":"datapoint","schema_id":"item_net_unit_price","page":1,"position":[714,846,768,870],"rir_position":null,"rir_confidence":null,"value":"1532.02","validation_sources":["human"],"type":"number"}]}]}]}]}
All connector endpoints, representing particular points in the
document lifetime, are simple verbs that receive a JSONPOSTed and
potentially expect a JSON returned in turn.
POST
The authorization type and authorization token is passed as anAuthorizationHTTP header. Authorization type may besecret_key(shared secret) orBasicforHTTP basic authentication.
Authorization
secret_key
Basic
Please note that for Basic authentication,authorization_tokenis passed
as-is, therefore it must be set to a correct base64 encoded value. For example
usernameconnectorand passwordsecure123is encoded asY29ubmVjdG9yOnNlY3VyZTEyMw==authorization token.
authorization_token
connector
secure123
Y29ubmVjdG9yOnNlY3VyZTEyMw==
Connector requests may be authenticated using a client SSL certificate, seeConnectorAPI for reference.

#### Errors

If a connector does not implement an endpoint, it may return HTTP status 404.
An endpoint may fail, returning either HTTP 4xx or HTTP 5xx; for some endpoints
(like validate and save), this may trigger a user interface message;
either theerrorkey of a JSON response is used, or the response body
itself in case it is not JSON. The connector endpoint save can be called
in asynchronous (default) as well as synchronous mode (useful forembedded mode).

#### Data format

The received JSON object contains two keys,metacarrying the metadata andcontentcarrying endpoint-specific content.
meta
content
The metadata identify the concerned document, containing attributes:
KeyTypeDescriptiondocument_urlURLdocumentURLarrived_attimestampA time of document arrival in Rossum (ISO 8601)original_fileURLPermanent URL for the documentoriginal fileoriginal_filenamestringFilename of the document on arrival in Rossumqueue_namestringName of the document's queueworkspace_namestringName of the document's workspaceorganization_namestringName of the document's organizationannotationURLAnnotation URLqueueURLDocument's queue URLworkspaceURLDocument's workspace URLorganizationURLDocument's organization URLmodifierURLModifier URLmodifier_metadataobjectMetadata attribute of the modifier, seemetadataqueue_metadataobjectMetadata attribute of the queue, seemetadataannotation_metadataobjectMetadata attribute of the annotation, seemetadatarir_poll_idstringInternal extractor processing idupdated_datapoint_idslist[string]Ids of objects that were recently modified by userautomatedboolFlag whether annotation wasautomated
A common class of content is theannotation tree, which is a JSON object
that can contain nested datapoint objects, and matches the schema datapoint tree.
Intermediate nodes have the following structure:
KeyTypeDescriptionidintegerA unique id of the given nodeschema_idstringReference mapping the node to the schema treecategorystringOne ofsection,multivalue,tuplechildrenlistA list of other nodes
Datapoint (leaf) nodes structure contains actual data:
KeyTypeDescriptionidintegerA unique id of the given nodeschema_idstringReference mapping the node to the schema treecategorystringdatapointtypestringOne ofstring,dateornumber, as specified in theschemavaluestringThe datapoint value, string represented but normalizes, to that they are machine readable: ISO format for dates, a decimal for numberspageintegerA 1-based integer index of the page, optionalpositionlist[float]List of four floats describing the x1, y1, x2, y2 bounding box coordinatesrir_positionlist[float]Bounding box of the value as detected by the data extractor. Format is the same as forposition.rir_confidencefloatConfidence (estimated probability) that this field was extracted correctly.
position
meta
content

#### Annotation lifecycle with a connector

If an asynchronous connector is deployed to a queue, an annotation status will change fromreviewingtoexportingand subsequently toexportedorfailed_export. If no connector extension is deployed to a queue or if the attributeasynchronousis set tofalse, an annotation status will change fromreviewingtoexported(orfailed_export) directly.
reviewing
exporting
exported
failed_export
asynchronous
false
reviewing
exported
failed_export

### Endpoint: validate

This endpoint is called after the document processing has finished, when operator opens a document
in the Rossum verification interface and then every time after operator updates a field. After the
processing is finished, the initial validate call is marked withinitial=trueURL parameter.
For the other calls, only/validatewithout the parameter is called. Note that after document processing, initial 
validation is followed bybusiness rulesexecution for bothvalidationandannotation_importedevents.
initial=true
/validate
validation
annotation_imported
The request path is fixed to/validateand cannot be changed.
/validate
It may:
- validate the given annotation tree and return a list of messages commenting on it
(e.g. pointing out errors or showing matched suppliers).
- update the annotation tree by returning a list of replace, add and remove operations
Both the messages and the updated data are shown in the verification
interface. Moreover, the messages may block confirmation in the case of errors.
This endpoint should be fast as it is part of an interactive workflow.
Receives an annotation tree ascontent.
Returns a JSON object with the lists:messages,operationsandupdated_datapoints.
messages
operations
updated_datapoints

#### Keysmessages,operations(optional)

messages
operations
The description of these keys was moved to theHook Extension. See the descriptionhere.

#### Keyupdated_datapoints(optional, deprecated)

updated_datapoints
We also support a simplified version of updates usingupdated_datapointsresponse key. It only supports updates (no add or remove operations) and is now
deprecated. The updated datapoint object contains attributes:
updated_datapoints
KeyTypeDescriptionidstringA unique id of the relevant datapoint, currently only datapoints of categorydatapointcan be updatedvaluestringNew value of the datapoint. Value is formatted according to the datapoint type (e.g. date is string representation of ISO 8601 format).hiddenbooleanToggle for hiding/showing of the datapoint, seedatapointoptionslist[object]Options of the datapoint -- valid only fortype=enum, seeenum optionspositionlist[float]New position of the datapoint, list of four numbers.
datapoint
type=enum
Validate endpoint should always return200 OKstatus.
Anerrormessage returned from the connector prevents user from confirming the document.

### Endpoint: save

This endpoint is called when the invoice transitions to theexportedstate.
Connector may process the final document annotation and save it to the target
system. It receives an annotation tree ascontent. The request path is fixed
to/saveand cannot be changed.
exported
content
/save
The save endpoint is called asynchronously (unless synchronous mode is set) in
relatedconnector object. Timeout of the save endpoint is 60
seconds.
reviewing
exporting
exported
For successful export, the request should have2xxstatus.
Example of successfulsaveresponse without messages in UI
save

```
HTTP/1.1204No Content
```

HTTP/1.1204No Content

```
HTTP/1.1200OKContent-Type:text/plainthis response body is ignored
```

HTTP/1.1200OKContent-Type:text/plainthis response body is ignored

```
HTTP/1.1200OKContent-Type:application/json{"messages":[]}
```

HTTP/1.1200OKContent-Type:application/json{"messages":[]}
When messages are expected to be displayed in the UI, they should be sent in the
same format as invalidate endpoint.
Example of successfulsaveresponsewithmessages in UI
save

```
HTTP/1.1200OKContent-Type:application/json{"messages":[{"content":"Everything is OK.","id":null,"type":"info"}]}
```

HTTP/1.1200OKContent-Type:application/json{"messages":[{"content":"Everything is OK.","id":null,"type":"info"}]}
If the endpoint fails with an HTTP error and/or message of typeerroris received,
the document transitions to thefailed_exportstate - it is then available
to the operators for manual review and re-queuing to theto_reviewstate
in the user interface. Re-queuing may be done also programmatically via
the API using a PATCH call to setto_reviewannotation status. Patching
annotation status toexportingstate triggers an export retry.
error
failed_export
to_review
to_review
exporting
Example of unsuccessfulsaveresponsewithmessages in UI
save

```
HTTP/1.1422Unprocessable EntityContent-Type:application/json{"messages":[{"content":"Even though this message is info, the export will fail due to the status code.","id":null,"type":"info"}]}
```

HTTP/1.1422Unprocessable EntityContent-Type:application/json{"messages":[{"content":"Even though this message is info, the export will fail due to the status code.","id":null,"type":"info"}]}

```
HTTP/1.1500Internal Server ErrorContent-Type:text/plainAn errror message "Export failed." will show up in the UI
```

HTTP/1.1500Internal Server ErrorContent-Type:text/plainAn errror message "Export failed." will show up in the UI

```
HTTP/1.1200OKContent-Type:application/json{"messages":[{"content":"Proper status code could not be set.","id":null,"type":"error"}]}
```

HTTP/1.1200OKContent-Type:application/json{"messages":[{"content":"Proper status code could not be set.","id":null,"type":"error"}]}


## Custom UI Extension

Sometimes users might want to extend the behavior of UI validation view with something special. That should be the goal of custom UI extensions.

### Buttons

Currently, there are two different ways of using a custom button:
- Popup Button - opens a specific URL in the web browser
- Validate Button - triggers a standard validate call to connector
If you would like to read more about how to create a button, see theButton schema.

#### Popup Button

Popup Button opens a website completely managed by the user in a separate tab. It runs in parallel to the validation interface session in the app. Such website can be used for any interface that will assist operators in the reviewing process.
Example Use Cases of Popup Button:
- opening an email linked to the annotated document
- creating a new item in external database according to extracted data
You can communicate with the validation interface directly
using standard browser API of window.postMessage.
You will need to use window.addEventListeners in order to receive messages
from the validation interface:

```
window.addEventListener('message',({data:{type,result}})=>{// logic});
```

window.addEventListener('message',({data:{type,result}})=>{// logic});
The shape of theresultkey is the same as the top levelcontentattribute of theannotation dataresponse.
result
content
Once the listener is in place, you can post one of supported message types:
- GET_DATAPOINTS- returns the same tree structure you’d get by requesting annotation data
GET_DATAPOINTS

```
window.opener.postMessage({type:'GET_DATAPOINTS'},'https://<example>.rossum.app')
```

window.opener.postMessage({type:'GET_DATAPOINTS'},'https://<example>.rossum.app')
- UPDATE_DATAPOINT- sends updated value to a Rossum datapoint. Only one datapoint value can be updated
at a time.
UPDATE_DATAPOINT

```
window.opener.postMessage({type:'UPDATE_DATAPOINT',data:{id:DATAPOINT_ID,value:"Updated value"}},'https://<example>.rossum.app')
```

window.opener.postMessage({type:'UPDATE_DATAPOINT',data:{id:DATAPOINT_ID,value:"Updated value"}},'https://<example>.rossum.app')
- FINISH- informs the Rossum app that the popup process is ready to be closed.
After this message is posted, popup will be closed and Rossum app will trigger a validate call.
FINISH

```
window.opener.postMessage({type:'FINISH'},'https://<example>.rossum.app');
```

window.opener.postMessage({type:'FINISH'},'https://<example>.rossum.app');
Providing message type to postMessage lets Rossum interface know what operation
user requests and determines the type of the answer which could be used to
match appropriate response.

#### Validate button

Ifpopup_urlkey is missing in button’s schema, clicking the button will trigger a standard validate call to connector. In such call,updated_datapoint_idswill contain the ID of the pressed button.
popup_url
updated_datapoint_ids
Note: if you’re missing some annotation data that you’d like to receive in a similar way, do contact our support team. We’re collecting feedback to further expand this list.


## Extension Logs

For easy and efficient development process of the extensions, our backend logsrequests,responses(if enabled) and
additional information, when the hook is being called.
requests
responses

### Hook Log

The hook log objects consist of following attributes, where it also differentiates between the hook events as follows:

#### Base Hook Log object

These attributes are included in all the logs independent of the hook event
KeyTypeDescriptionOptionaltimestamp*strTimestamp of the log-recordrequest_idUUIDHookcall request IDeventstringHook'seventactionstringHook'sactionorganization_idintID of the associatedOrganization.queue_idintID of the associatedQueue.truehook_idintID of the associatedHook.hook_typestrHook type. Possible values:webhook,functionlog_levelstrLog-level. Possible values:INFO,ERROR,WARNINGmessagestrA log-messagerequeststrRaw request sent to the HooktrueresponsestrRaw response received from the Hooktrue
webhook
function
INFO
ERROR
WARNING
*Timestamp is of the ISO 8601 format with UTC timezone e.g.2023-04-21T07:58:49.312655
2023-04-21T07:58:49.312655

#### Annotation Content or Annotation Status Hook Events

In addition to the Base Hook Log object, theannotation contentandannotation statusevent hook logs contains
the following attributes:
annotation content
annotation status
KeyTypeDescriptionOptionalannotation_idintID of the associatedAnnotation.true

#### Email Hook Events

In addition to the Base Hook Log object, theemailevent hook logs contains the following attributes:
email
KeyTypeDescriptionOptionalemail_idintID of the associatedEmail.true


## Source IP Address ranges

Rossum will use these source IP addresses for outgoing connections to your
services (e.g. when sending requests to a webhook URL):
Europe (Ireland):
- 34.254.110.123
- 52.209.175.153
- 54.217.193.239
- 54.246.127.143
Europe 2 (Frankfurt):
- 3.75.26.254
- 3.126.211.68
- 3.126.98.96
- 3.76.159.143
US (N. Virginia):
- 3.222.161.192
- 50.19.104.88
- 52.2.120.212
- 18.213.174.191
JP (Tokyo):
- 3.115.38.171
- 35.74.141.62
- 35.75.49.12
- 52.194.128.167
You can use the list to limit incoming connections on a firewall. The list may be
updated eventually, please update your configuration at least once per three months.
If you have a customer-specific deployment, contact Rossum support for a specific IP list.


# Rossum Transaction Scripts

The Rossum platform can evaluate snippets of Python code that can manipulate
business transactions processed by Rossum - Transaction Scripts (or TxScripts).
The principal use of these TxScript snippets is
to automatically fill in computed values offormulatype fields.
The code can be also evaluated as a serverless function based extension that is
hooked to theannotation_contentevent.
formula
annotation_content
The TxScript Python environment is based on Python 3.12 or newer,
in addition including a variety of additional predefined functions and variables.
The environment has been designed so that code operating on Rossum objects
is very short, easy to read and write by both humans and LLMs, and many simple
tasks are doable even by non-programmers (who could however e.g. build
an Excel spreadsheet).
The environment is special in the following ways:
- Predefined variables allowing easy access to Rossum objects.
Predefined variables allowing easy access to Rossum objects.
- Some environment-specific helper functions and aliases.
Some environment-specific helper functions and aliases.
- How code is evaluated specifically in formula field context to yield a computed value.
How code is evaluated specifically in formula field context to yield a computed value.
annotation_content
The TxScript environment provides accessors to Rossum objects associated with
the event that triggered the code evaluation.
The event context is generally available through atxscript.TxScriptobject;
calling the object methods and modifying the attributes (such as raising
messages or modifying field values) controls the event hook response.
txscript.TxScript
Example of a no-op serverless function instantiating theTxScriptobject
TxScript

```
fromtxscriptimportTxScriptdefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)print(t)returnt.hook_response()
```

fromtxscriptimportTxScriptdefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)print(t)returnt.hook_response()
In serverless functions,
this object must be explicitly imported and instantiated using a.from_payload()function.  The.hook_response()method yields a dict representing the
prescribed event hook response (with keys such as"messages","operations"etc.) that can be directly returned from the handler.
.from_payload()
.hook_response()
"messages"
"operations"
Meanwhile, in formula fields it is instantiated automatically and its existence is
entirely transparent to the developer as the object's attributes and methods are
directly available as globals of the formula fields code.
txscript
pip install txscript


## Pythonized Rossum objects

The TxScript environment provides instances of several pertinent Rossum objects.
These instances are directly available in globals namespace in formula fields, and
as atributes of theTxScriptinstance within serverless functions.
TxScript

### Fields Object

Afieldobject is provided that allows access to the fields of
annotation content.
field

#### Attributes

Object attributes correspond to annotation fields, e.g.field.amount_totalwill evaluate
to the value of theamount_totalfield. The attributes behave specially:
field.amount_total
amount_total
- The field value types are pythonized. String fields arestrtype, number fields
arefloattype, date fields aredatetime.dateinstances.
The field value types are pythonized. String fields arestrtype, number fields
arefloattype, date fields aredatetime.dateinstances.
str
float
datetime.date
- Since number fields are of typefloat, they should always be rounded when tested for
equality (because e.g. 0.1 + 0.2 isn't exactly 0.3 in floating-point arithmetics):round(field.amount_total, 2) == round(field.amount_total_base, 2)
Since number fields are of typefloat, they should always be rounded when tested for
equality (because e.g. 0.1 + 0.2 isn't exactly 0.3 in floating-point arithmetics):round(field.amount_total, 2) == round(field.amount_total_base, 2)
float
round(field.amount_total, 2) == round(field.amount_total_base, 2)
In other words, this expression referencing table columns will behave intuitively:

```
ifall(notis_empty(field.item_amount_base.all_values)):sum(default_to(field.item_amount_tax.all_values,0)*0.9+field.item_amount_base.all_values)
```

ifall(notis_empty(field.item_amount_base.all_values)):sum(default_to(field.item_amount_tax.all_values,0)*0.9+field.item_amount_base.all_values)
- You can access all in-multivalue field ids (table columns or simple multivalues)
via the.all_valuesproperty (e.g.field.item_amount.all_values). Its value
is a special sequence objectTableColumnthat behaves similarly to alist,
but with operators applying elementwise or distributive to scalars (NumPy-like).
Outside a single row context, the.all_valuesproperty is the only legal way
to work with these field ids. It is also a way to access a row of another multivalue 
from a multivalue formula.
.all_values
field.item_amount.all_values
TableColumn
list
.all_values
Example of iterating over rows in a formula field

```
forrowinfield.line_items:ifnotis_empty(row.item_amount)androw.item_amount<0:show_warning("Negative amount",row.item_amount)
```

forrowinfield.line_items:ifnotis_empty(row.item_amount)androw.item_amount<0:show_warning("Negative amount",row.item_amount)
Example of iterating over rows in serverless function hook

```
fromtxscriptimportTxScript,is_emptydefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)forrowint.field.line_items:ifnotis_empty(row.item_amount)androw.item_amount<0:t.show_warning("Negative amount",row.item_amount)returnt.hook_response()
```

fromtxscriptimportTxScript,is_emptydefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)forrowint.field.line_items:ifnotis_empty(row.item_amount)androw.item_amount<0:t.show_warning("Negative amount",row.item_amount)returnt.hook_response()
- You can access individual multivalue tuple rows by accessing the multivalue or tuple field id,
which provides a list offield-like objects that provide in-row tuple field members
as attributes named by their field id.
You can access individual multivalue tuple rows by accessing the multivalue or tuple field id,
which provides a list offield-like objects that provide in-row tuple field members
as attributes named by their field id.
field
- Whilefield.amount_totalevaluates to a float-like value (or other types),
the value also provides anattrattribute that gives access to all
field schema, field object value and field object value content API object attributes
(i.e. one can writefield.amount_total.attr.rir_confidence).  Attributesposition,page,validation_sources,hiddenandoptionsare read-write.
Whilefield.amount_totalevaluates to a float-like value (or other types),
the value also provides anattrattribute that gives access to all
field schema, field object value and field object value content API object attributes
(i.e. one can writefield.amount_total.attr.rir_confidence).  Attributesposition,page,validation_sources,hiddenandoptionsare read-write.
field.amount_total
attr
field.amount_total.attr.rir_confidence
position
page
validation_sources
hidden
options
- Fields that are not set (or are in an error state due to an invalid value)
evaluate to aNone-like value (except strings which evaluate to""),
but because of the above they are in fact not pure PythonNones. Therefore,
theymust notbe tested for usingis None. Instead, convenience helpersis_empty(field.amount_total)anddefault_to(field.amount_total, 0)should be used.
These helpers also behave correctly on string fields as well.
Fields that are not set (or are in an error state due to an invalid value)
evaluate to aNone-like value (except strings which evaluate to""),
but because of the above they are in fact not pure PythonNones. Therefore,
theymust notbe tested for usingis None. Instead, convenience helpersis_empty(field.amount_total)anddefault_to(field.amount_total, 0)should be used.
These helpers also behave correctly on string fields as well.
None
""
None
is None
is_empty(field.amount_total)
default_to(field.amount_total, 0)
Example of updating field values in a serverless function hook

```
fromtxscriptimportTxScript,is_empty,default_todefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)ifnotis_empty(t.field.amount_tax_base):# Note: This type of operation is strongly discouraged in serverless# functions, since the modification is non-transparent to the user and# it is hard to trace down which hook modified the field.# Always prefer making amount_total a formula field!t.field.amount_total=t.field.amount_tax_base+default_to(t.field.amount_tax,0)# Merge po_number_external to the po_numbers multivalueifnotis_empty(t.field.po_number_external):t.field.po_numbers.all_values.remove(t.field.po_number_external)t.automation_blocker("External PO",t.field.po_numbers)else:t.field.po_number_external.attr.hidden=True# Filter out non-empty line items and add a discount line itemt.field.line_items=[rowforrowint.field.line_itemsifnotis_empty(row.item_amount)]if"10% discount"int.field.termsandnotis_empty(t.field.amount_total):t.field.line_items.append({"item_amount":-t.field.amount_total*0.1,"item_description":"10% discount"})t.field.line_items[-1].item_amount.attr.validation_sources.append("connector")t.field.line_items[-1].item_description.attr.validation_sources.append("connector")t.field.po_match.attr.options=[{"label":f"PO:{po}","value":po}forpoint.field.po_numbers.all_values]t.field.po_match.attr.options+=t.field.default_po_enum.attr.options# Update the currently selected enum option if the value fell out of the listif(len(t.field.po_match.attr.options)>0andt.field.po_matchnotin[po.valueforpoint.field.po_match.attr.options]):t.field.po_match=t.field.po_match.attr.options[0].valuereturnt.hook_response()
```

fromtxscriptimportTxScript,is_empty,default_todefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)ifnotis_empty(t.field.amount_tax_base):# Note: This type of operation is strongly discouraged in serverless# functions, since the modification is non-transparent to the user and# it is hard to trace down which hook modified the field.# Always prefer making amount_total a formula field!t.field.amount_total=t.field.amount_tax_base+default_to(t.field.amount_tax,0)# Merge po_number_external to the po_numbers multivalueifnotis_empty(t.field.po_number_external):t.field.po_numbers.all_values.remove(t.field.po_number_external)t.automation_blocker("External PO",t.field.po_numbers)else:t.field.po_number_external.attr.hidden=True# Filter out non-empty line items and add a discount line itemt.field.line_items=[rowforrowint.field.line_itemsifnotis_empty(row.item_amount)]if"10% discount"int.field.termsandnotis_empty(t.field.amount_total):t.field.line_items.append({"item_amount":-t.field.amount_total*0.1,"item_description":"10% discount"})t.field.line_items[-1].item_amount.attr.validation_sources.append("connector")t.field.line_items[-1].item_description.attr.validation_sources.append("connector")t.field.po_match.attr.options=[{"label":f"PO:{po}","value":po}forpoint.field.po_numbers.all_values]t.field.po_match.attr.options+=t.field.default_po_enum.attr.options# Update the currently selected enum option if the value fell out of the listif(len(t.field.po_match.attr.options)>0andt.field.po_matchnotin[po.valueforpoint.field.po_match.attr.options]):t.field.po_match=t.field.po_match.attr.options[0].valuereturnt.hook_response()
- You can assign values to the field attributes and modify the multivalue lists,
which will be reflected back in the app once your hook finishes.  (This is not
permitted in the read-only context of formula fields.)  You may construct
values of tuple rows as dicts indexed by column schema ids.
You can assign values to the field attributes and modify the multivalue lists,
which will be reflected back in the app once your hook finishes.  (This is not
permitted in the read-only context of formula fields.)  You may construct
values of tuple rows as dicts indexed by column schema ids.
- You can modify thefield.*.attr.validation_sourceslist and it will be
reflected back in the app once your hook finishes.  It is not recommended
to perform any operation except.append("connector")(automates the field).
You can modify thefield.*.attr.validation_sourceslist and it will be
reflected back in the app once your hook finishes.  It is not recommended
to perform any operation except.append("connector")(automates the field).
field.*.attr.validation_sources
.append("connector")
- Forenumtype fields, you can modify thefield.*.attr.optionslist
and it will be reflected back in the app once your hook finishes.  Elements of
the list are objects with thelabelandvalueattribute each.  You may
construct new elements as dicts with thelabelandvaluekeys.
Forenumtype fields, you can modify thefield.*.attr.optionslist
and it will be reflected back in the app once your hook finishes.  Elements of
the list are objects with thelabelandvalueattribute each.  You may
construct new elements as dicts with thelabelandvaluekeys.
enum
field.*.attr.options
label
value
label
value
- Outside of formula fields, you may access fields dynamically by computed schema
id (for example based on configuration variables) by using standard Python'sgetattr(field, schema_id).  Note that inside formula fields, such dynamic
access is not supported as it breaks automatic dependency tracking and formula
field value would not be recomputed once the referred field value changes.
Outside of formula fields, you may access fields dynamically by computed schema
id (for example based on configuration variables) by using standard Python'sgetattr(field, schema_id).  Note that inside formula fields, such dynamic
access is not supported as it breaks automatic dependency tracking and formula
field value would not be recomputed once the referred field value changes.
getattr(field, schema_id)
- You may also access the parent of nested fields (within multivalues and/or
tuples) via their.parentattribute, or the enclosing multivalue field via.parent_multivalue.  This is useful when combined with thegetattrdynamic
field access.  For example, in the default Rossum schema naming setup,getattr(field, "item_quantity").parent_multivalue == field.line_items.
You may also access the parent of nested fields (within multivalues and/or
tuples) via their.parentattribute, or the enclosing multivalue field via.parent_multivalue.  This is useful when combined with thegetattrdynamic
field access.  For example, in the default Rossum schema naming setup,getattr(field, "item_quantity").parent_multivalue == field.line_items.
.parent
.parent_multivalue
getattr
getattr(field, "item_quantity").parent_multivalue == field.line_items

### Annotation Object

Anannotationobject is provided, representing the pertinent annotation.
annotation

#### Attributes

The  available attributes are:id,url,statusprevious_status,automated,automatically_rejected,einvoice,metadata,created_at,modified_at,exported_at,confirmed_at,assigned_at,export_failed_at,deleted_at,rejected_at,purged_at
id
url
status
previous_status
automated
automatically_rejected
einvoice
metadata
created_at
modified_at
exported_at
confirmed_at
assigned_at
export_failed_at
deleted_at
rejected_at
purged_at
The timestamp attributes, such ascreated_at, are represented as a pythondatetimeinstance.
created_at
datetime
Theraw_dataattribute is a dict containing all attributes
of theannotationAPI object.
raw_data
Theannotationalso has adocumentattribute. Thedocumentitself has the following attributes:id,url,arrived_at,created_at,original_file_name,metadata,mime-type, seedocumentfor more details.raw_datais also provided.
annotation
document
document
id
url
arrived_at
created_at
original_file_name
metadata
mime-type
raw_data
This enables txscript code such asannotation.document.original_file_name.
annotation.document.original_file_name
Theannotationalso has an optionalemailattribute. Theemailitself has the following attributes:id,url,created_at,last_thread_email_created_at,subject,email_from(identical tofromon API),to,cc,bcc,body_text_plain,body_text_html,metadata,annotation_counts,type,labels,filtered_out_document_count, seeemailfor more details.raw_datais also provided.
annotation
email
email
id
url
created_at
last_thread_email_created_at
subject
email_from
from
to
cc
bcc
body_text_plain
body_text_html
metadata
annotation_counts
type
labels
filtered_out_document_count
raw_data
This enables txscript code such asannotation.email.subject.
annotation.email.subject

#### Methods

Example ofrejectingan annotation

```
fromtxscriptimportTxScriptdefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)ifround(t.field.amount_total)!=round(t.field.amount_total_base+t.field.amount_tax):annotation.action("reject",note_content="Amounts do not match")ift.field.amount_total>100000:annotation.action("postpone")returnt.hook_response()
```

fromtxscriptimportTxScriptdefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)ifround(t.field.amount_total)!=round(t.field.amount_total_base+t.field.amount_tax):annotation.action("reject",note_content="Amounts do not match")ift.field.amount_total>100000:annotation.action("postpone")returnt.hook_response()
Theaction(verb: str, **args)method issues aPOSTon theannotationAPI object for a given verb in the formPOST /v1/annotations/{id}/{verb}, passing
additional arguments as specified.
(Notable verbs arereject,postponeanddelete.)
action(verb: str, **args)
POST
POST /v1/annotations/{id}/{verb}
reject
postpone
delete
Note that Rossum authorization token passing must be enabled on the hook.


## TxScript Functions

Several functions are provided that map 1:1 to common extension hook return values.
These functions are directly available in globals namespace in formula fields, and
as methods of theTxScriptinstance within serverless functions.
TxScript
Example of raising a message in a formula field

```
iffield.date_issue<date(2024,1,1):show_warning("Issue date long in the past",field.date_issue)
```

iffield.date_issue<date(2024,1,1):show_warning("Issue date long in the past",field.date_issue)
Example of raising a message in serverless function hook

```
fromtxscriptimportTxScriptdefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)ift.field.date_issue<date(2024,1,1):t.show_warning("Issue date long in the past",field.date_issue)returnt.hook_response()
```

fromtxscriptimportTxScriptdefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)ift.field.date_issue<date(2024,1,1):t.show_warning("Issue date long in the past",field.date_issue)returnt.hook_response()
Theshow_error(),show_warning()andshow_info()functions raise a message,
either document-wide or attached to a particular field.  As arguments, they take
the message text (contentkey) and optionally the field to attach the message to
(converted to theidkey).  If no field is passed or if the field references 
a multivalue column, a document-level message is created.
show_error()
show_warning()
show_info()
content
id
For example, you may useshow_error()for fatals like a missing required field,
whereasshow_info()is suitable to decorate a supplier company id with its name
as looked up in the suppliers database.
show_error()
show_info()
Example of a formula raising an automation blocker

```
ifnotis_empty(field.amount_total)andfield.amount_total<0:automation_blocker("Total amount is negative",field.amount_total)
```

ifnotis_empty(field.amount_total)andfield.amount_total<0:automation_blocker("Total amount is negative",field.amount_total)
Theautomation_blocker()function analogously
raises an automation blocker, creatingautomation blockersoftypeextensionand therefore stopping theautomationwithout the need to create an error message.
The function signature is the same as for the show... methods above.
automation_blocker()
extension


## Helper Functions and Aliases

Whenever a helper function is available, it should be used preferentially.
This is for the sake of better usability for admin users, but also because
these functions are e.g. designed to seamlessly work withTableColumninstances.
TableColumn
All identifiers below are directly available in globals namespace in formula fields.
Within serverless functions, they can be imported asfrom txscript import ...(or all of them obtained viafrom txscript import *).
from txscript import ...
from txscript import *

### Helper Functions

Theis_empty(field.amount_total)boolean function returns True if the given
field has no value set. Use this instead of testing for None.
is_empty(field.amount_total)
Thedefault_to(field.order_id, "INVALID")returns either the field value,
or a fallback value (string INVALID in this example) in case it is not set.
default_to(field.order_id, "INVALID")

### Convenience Aliases

All string manipulations should be performed usingsubstitute(...),
which is an alias forre.sub.
substitute(...)
re.sub
These identifiers are automatically imported:
from datetime import date, timedelta
from datetime import date, timedelta
import re
import re


## Formula Fields

The Rossum Transaction Scripts can be evaluated in the context of
a formula-type field to automatically compute its value.
In this context, thefieldobject is read-only, i.e. side-effects on
values of other fields are prohibited (though you can still attach a message
or automation blocker to another field).
Theannotationobject is not available.
field
annotation
This example sets the formula field value to either 0 or the output of the
specified regex substitution.

```
iffield.order_id=="INVALID":show_warning("Falling back to zero",field.order_id)"0"else:substitute(r"[^0-9]",r"",field.order_id)
```

iffield.order_id=="INVALID":show_warning("Falling back to zero",field.order_id)"0"else:substitute(r"[^0-9]",r"",field.order_id)
The Python code is evaluated just as Python's interactive mode would run it,
using the last would-be printed value as the formula field value. In other words,
the value of the last evaluated expression in the code is used as the new value
of the field.
In case the field is within a multivalue tuple, it is evaluated for each
cell of that column, i.e. within each row.  Referring to other fields within
the row via thefieldobject accesses the value of the respective single row cell
(just like therowobject when iterating over multivalue tuple rows).  Referring
to fields outside the multivalue tuple via thefieldobject still works as usual.
Thus, in a definition offield.item_amountformula,field.item_quantityrefers
to the quantity value of the current row, while you can still also accessfield.amount_totalheader field.  Further,field._indexprovides the row number.
field
row
field
field.item_amount
field.item_quantity
field.amount_total
field._index
Field dependencies of formula fields are determined automatically.  The only caveat
is that in case you iterate over line item rows within the formula field code, you
must name your iteratorrow.
row


# Automation

All imported documents are processed by the data extraction process to obtain
values of fields specified in theschema. Extracted values are then
available for validation in the UI.
Usingper-queue automation settings, it is possible to skip manual UI
validation step and automatically switch document to confirmed state or proceed with the export of the document.
Decision to export document or switch it to confirmed state is based onQueuesettings.
Currently, there are three levels of automation:
- No automation: User has to review all documents in the UI to validate
extracted data (default).
No automation: User has to review all documents in the UI to validate
extracted data (default).
- Confidence automation: User only reviews documents with low data extraction
confidence ("tick" icon is not displayed for one or more fields) or
validation errors. By default, we automate documents that are duplicates and do not automate documents that edits (split) is proposed. You can change this inper-queue automation settings
Confidence automation: User only reviews documents with low data extraction
confidence ("tick" icon is not displayed for one or more fields) or
validation errors. By default, we automate documents that are duplicates and do not automate documents that edits (split) is proposed. You can change this inper-queue automation settings
- Full automation: All documents with no validation errors are exported or switched to confirmed state only if they do not contain a suggested edit (split). You can change this inper-queue automation settingsAn error triggered by a schema field constraint or connector validation
blocks auto-export even in full-automation level. In such case, non-required
fields with validation errors are cleared and validation is performed again.
In case the error persists, the document must be reviewed manually, otherwise
it is exported or switched to confirmed state.
Full automation: All documents with no validation errors are exported or switched to confirmed state only if they do not contain a suggested edit (split). You can change this inper-queue automation settingsAn error triggered by a schema field constraint or connector validation
blocks auto-export even in full-automation level. In such case, non-required
fields with validation errors are cleared and validation is performed again.
In case the error persists, the document must be reviewed manually, otherwise
it is exported or switched to confirmed state.
Read more about theAutomation frameworkon our developer hub.

### Sources of field validation

Low-confidence fields are marked in the UI by an "eye" icon, we consider them
to be notvalidated. On the API level they have an emptyvalidation_sourceslist.
validation_sources
Validation of a field may be introduced by various sources: data extraction
confidence above a threshold, computation of various checksums (e.g. VAT rate,
net amount and gross amount) or a human review. These validations are recorded in
thevalidation_sourcelist. The data extraction confidence threshold may be
adjusted, seevalidation sourcesfor details.
validation_source

### AI Confidence Scores

While there are multiple ways to automatically pre-validate fields, the most
prominent one is score-based validation based on AI Core Engine confidence
scores.
The confidence score predicted for each AI-extractd field is stored in therir_confidenceattribute. The score is a number between 0 and 1, and is
calibrated in such a way that it corresponds to the probability of a given
value to be correct. In other words, a field with score 0.80 is expected
to be correct 4 out of 5 times.
rir_confidence
The value of thescore_threshold(can be set onqueue,
or individually perdatapointin schema; default is 0.8)
attribute represents the minimum score that triggers
automatic validation. Because of the score meaning, this directly corresponds
to the achieved accuracy. For example, if a score threshold for validation is
set at 0.8, that gives an expected error rate of 20% for that field.
score_threshold


## Autopilot

Autopilot is a automatic process removing "eye" icon from fields.
This process is based on past occurrence of field value on documents which has been
already processed in the same queue.
Read more about thisAutomation componenton our developer hub.

### Autopilot configuration

Default Autopilot configuration

```
{"autopilot":{"enabled":true,"search_history":{"rir_field_names":["sender_ic","sender_dic","account_num","iban","sender_name"],"matching_fields_threshold":2},"automate_fields":{"rir_field_names":["account_num","bank_num","iban","bic","sender_dic","sender_ic","recipient_dic","recipient_ic","const_sym"],"field_repeated_min":3}}}
```

{"autopilot":{"enabled":true,"search_history":{"rir_field_names":["sender_ic","sender_dic","account_num","iban","sender_name"],"matching_fields_threshold":2},"automate_fields":{"rir_field_names":["account_num","bank_num","iban","bic","sender_dic","sender_ic","recipient_dic","recipient_ic","const_sym"],"field_repeated_min":3}}}
Autopilot configuration can be modified inQueue.settingswhere you can set
rules for each queue.
If Autopilot is not explicitly disabled by switchenabledset tofalse, Autopilot is enabled.
enabled
false
Configuration is divided into two sections:

#### History search

This section configures process of finding documents from the same sender as the document which is currently being processed.
Annotation is considered from the same sender if it contains fields with samerir_field_nameand value as the current document.
When at least two fields listed inrir_field_namesmatch values of the current document, document is is considered to have same sender
rir_field_names

```
{"search_history":{"rir_field_names":["sender_ic","sender_dic","account_num"],"matching_fields_threshold":2}}
```

{"search_history":{"rir_field_names":["sender_ic","sender_dic","account_num"],"matching_fields_threshold":2}}
AttributeTypeDescriptionrir_field_nameslistList ofrir_field_namesused to find annotations from the same sender. This should contain fields which are unique for each sender. For examplesender_icorsender_dic.Please note that due to technical reasons it is not possible to usedocument_typein this field and it will be ignored.matching_fields_thresholdintAt leastmatching_fields_thresholdfields must match current annotation in order to be considered from the same sender. See example on the right side.
sender_ic
sender_dic
document_type
matching_fields_threshold

#### Automate fields

This section describes rules which will be applied on annotations found in previous stepHistory search.
Field will have "eye" icon removed, if we have found at leastfield_repeated_minfields with samerir_field_nameand value
on documents found in stepHistory search.
field_repeated_min
AttributeTypeDescriptionrir_field_nameslistList ofrir_field_nameswhich can be validated based on past occurrencefield_repeated_minintNumber of times field must be repeated in order to be validated
If any config section is missing, default value which you can see on the right side is applied.


# Using Triggers

Trigger REST operations can be foundhere
When an event occurs, all triggers of that type will perform actions of their related objects:
Related objectActionDescriptionEmail templateSend email with the template to the event triggerer ifautomate=trueAutomatically respond to document vendors based on the document's content. The document has to come from an emailDelete recommendationsStop automation if one of the validation rules applies to the processed documentBased on the user's rules for delete recommendations, stop automation for the document which applies to these rules. The document requires manual evaluation
automate=true


## Trigger Event Types

Trigger objects can have one of the following event types
Trigger Event typeDescription (Trigger for an event of)email_with_no_processable_attachmentsAn Email has been received without any processable attachmentsannotation_createdProcessing of the Annotation started (Rossum received the Annotation)annotation_importedAnnotation data have been extracted by Rossumannotation_confirmedAnnotation was checked and confirmed by user (or automated)annotation_exportedAnnotation was exportedvalidationDocument is being validated

### Trigger Events Occurrence Diagram

To show an overview of the Trigger events and when they are happening, this diagram was created.


## Trigger Condition

Simple condition validating the presence ofvendor_idequal toMeat ltd.
vendor_id
Meat ltd.

```
{"$and":[{"field.vendor_id":{"$and":[{"$exists":true},{"$regex":"Meat ltd\\."}]}}]}
```

{"$and":[{"field.vendor_id":{"$and":[{"$exists":true},{"$regex":"Meat ltd\\."}]}}]}
Any required field is missing

```
{"$and":[{"required_field_missing":true}]}
```

{"$and":[{"required_field_missing":true}]}
At least one of theiban,date_due, andsender_vat_idfields is missing
iban
date_due
sender_vat_id

```
{"$and":[{"missing_fields":{"$elemMatch":{"$in":["iban","date_due","sender_vat_id"]}}}]}
```

{"$and":[{"missing_fields":{"$elemMatch":{"$in":["iban","date_due","sender_vat_id"]}}}]}
Will match if a required field is missing in the annotation, and the annotation contains avendor_idfield with a value that does matchMilk( inc\.)?regex. Or in other words, the trigger will activate if the Milk company sent us an invoice with missing data
vendor_id
Milk( inc\.)?

```
{"$and":[{"field.vendor_id":{"$and":[{"$exists":true},{"$regex":"Milk( inc\\.)?"}]}},{"required_field_missing":true}]}
```

{"$and":[{"field.vendor_id":{"$and":[{"$exists":true},{"$regex":"Milk( inc\\.)?"}]}},{"required_field_missing":true}]}
Will match if at least one of thedocument_type(Receipt,Other),language(CZ,EN,CH), orcurrency(USD,CZK) field match.
document_type
Receipt
Other
language
CZ
EN
CH
currency
USD
CZK

```
{"$or":[{"field.document_type":{"$in":["Receipt","Other"]},"field.language":{"$in":["CZ","EN","CH"]},"field.currency":{"$in":["CZK","USD"]}}]}
```

{"$or":[{"field.document_type":{"$in":["Receipt","Other"]},"field.language":{"$in":["CZ","EN","CH"]},"field.currency":{"$in":["CZK","USD"]}}]}
Will match if filename is a subset of the specified regular expression.

```
{"$or":[{"filename":{"$regex":"Milk( inc\\.)?"}}]}
```

{"$or":[{"filename":{"$regex":"Milk( inc\\.)?"}}]}
Will match if filename is a subset of one of the specified regular expressions.

```
{"$or":[{"filename":{"$or":[{"$regex":"Milk( inc\\.)?"},{"$regex":"Barn( inc\\.)?"}]}}]}
```

{"$or":[{"filename":{"$or":[{"$regex":"Milk( inc\\.)?"},{"$regex":"Barn( inc\\.)?"}]}}]}
Will match if a number of pages in the processed document is higher than the specified threshold.

```
{"$or":[{"number_of_pages":{"$gt":10}}]}
```

{"$or":[{"number_of_pages":{"$gt":10}}]}
A subset of MongoDB Query Language. The annotation will get converted into JSON records behind the scenes. The trigger gets activated if at least one such record matches the condition according to theMQL query rules. Anullcondition matches any record, just like{}. Record format:
null
{}

```
{
     "field": {
       "{schema_id}": string | null,
     },
     "required_field_missing": boolean,
     "missing_fields": string[],
   }
```

Supported MQL subset based on the trigger event type:
All trigger event types:

```
{}
```

Onlyannotation_imported,annotation_confirmed, andannotation_exportedtrigger event types:
annotation_imported
annotation_confirmed
annotation_exported

```
{
     "$and": [
       {"field.{schema_id}": {"$and": [{"$exists": true}, REGEX]}}
     ]
   }
```

Onlyannotation_importedtrigger event type:
annotation_imported

```
{
     "$and": [
       {"field.{schema_id}": {"$and": [{"$exists": true}, REGEX]}},
       {"required_field_missing": true},
       {"missing_fields": {"$elemMatch": {"$in": list[str[schema_id]]}}
     ]
   }
```

Onlyvalidationtrigger event type:
validation

```
{
     "$or": [
       {"field.document_type": {"$in": list[str[document_type]]},
       {"field.language": {"$in": list[str[language]]},
       {"field.currency": {"$in": list[str[currency]]},
       {"number_of_pages": {"$gt": 10},
       {"filename": REGEX}
     ]
   }
```


```
{
     "$or": [
       {"field.document_type": {"$in": list[str[document_type]]},
       {"field.language": {"$in": list[str[language]]},
       {"field.currency": {"$in": list[str[currency]]},
       {"number_of_pages": {"$gt": 10},
       {"filename": {"$or": [REGEX, REGEX]}
     ]
   }
```

FieldRequiredDescriptionfield.{schema_id}A field contained in the Annotation data. Theschema_idis theschemaid it got extracted underrequired_field_missingAny of theschema-required fields is missing. (*) Can not be combined withmissing_fieldsmissing_fieldsAt least one of theschemafields is missing. (*) Can not be combined withrequired_field_missingfield.{validation_field}A field contained a list of Delete Recommendation data. Thevalidation_fieldis theschemaid it got extracted undernumber_of_pagesA threshold value for the number of pages. A document with more pages is matched by the trigger.filenameThe filename or subset of filenames of the document is to match.REGEXtrueEither{"$regex": re2}or{"$not": {"$regex": re2}}**. Usesre2 regex syntax
schema_id
missing_fields
required_field_missing
validation_field
{"$regex": re2}
{"$not": {"$regex": re2}}
(*) A field is considered missing if any of the two following conditions is met
- the field hasui_configurationof typecapturedornulland no value was extracted for it andrir_cofidencescoreis at least 0.95
the field hasui_configurationof typecapturedornulland no value was extracted for it andrir_cofidencescoreis at least 0.95
captured
null
rir_cofidence
- the field hasui_configurationof other types (data,manual,formula, ...) and has an empty value
the field hasui_configurationof other types (data,manual,formula, ...) and has an empty value
data
manual
formula
(**) The$notoption for REGEX is not valid for thevalidationtrigger.
$not
validation


## Triggering Email Templates

Email template REST operations can be foundhere.
To set up email template trigger automation, link an email template object to a trigger object and set itsautomateattribute totrue. Currently, only one trigger can be linked. To set up the recipient(s) of the automated emails,
you can usebuilt-in placeholdersor direct values in theto,cc, andbccfields in email templates.
automate
true
to
cc
bcc
Only some email template types and some trigger event types can be linked together:
Template typeAllowed trigger eventscustom*email_with_no_processable_attachmentsemail_with_no_processable_attachmentsrejectionannotation_importedrejection_defaultannotation_imported
Email templates of typerejectionandrejection_defaultwill also reject the associated annotation when triggered.
rejection
rejection_default
Every newly created queue hasdefault email templates. Some of them have a trigger linked,
including an email template of typeemail_with_no_processable_attachmentswhich can not have its trigger unlinked
or linked to another trigger. To disable its automation, set itsautomateattribute tofalse.
email_with_no_processable_attachments
automate
false


## Triggering Validation

Delete Recommendation REST operations can be foundhere.
To set up validation trigger automation, specify the rules for validation and set its enabled attribute totrue.
true
This trigger is only valid for thevalidationtrigger event.
validation


## Hooks and Triggers Workflow

Sometimes it may happen that there is a need to know, what triggers and hooks and when are they run. That can be found in this workflow.


# Workflows

This feature must be explicitly enabled inqueue settings.


## Approval workflows

Approval workflows allow you to define multiple steps of approval process.
The workflow is started when the data extraction process is done (annotation isconfirmed) - it entersin_workflowstatus.
Then the annotation must beapprovedby defined approvers in order to be moved further (confirmedorexportedstatus).
in_workflow
confirmed
exported
The annotation is moved torejectedstatus if one of the assigneesrejectsit.
rejected
The current status of workflow is stored inworkflow runobject. All the events that happened during workflow can be tracked down byworkflow activityresources.


# Embedded Mode

In some use-cases, it is desirable to use only the per-annotation validation view of
the Rossum application.
Rossum may be integrated with other systems using so-calledembedded mode.
In embedded mode, special URL is constructed and then used in iframe or popup
browser window to show Rossum annotation view. Some view navigation widgets are hidden
(such ashome,postponeanddeletebuttons), so that user is only allowed to update
and confirm all field values.
Embedded mode can be used to view annotations only in status to_review, reviewing, postponed, or confirmed.
For security reasons it is strongly recommended to useannotator_embeddeduser rolefor this feature
as this user role has limited permissions to only be able to interact with resources necessary for embedded validation screen.
annotator_embedded


## Embedded mode workflow

The host application firstuploads a documentusing standard Rossum
API. During this process, anannotationobject
is created. It is possible to obtain astatusof the annotation object and wait for
the status to becometo_review(ready for checking) usingannotationendpoint.
to_review
As soon as importing of the annotation object has finished, an authenticated user
may callstart_embeddedendpoint to obtain a URL that is
to be included in iframe or popup browser window of the host application. Parameters of the call
arereturn_urlandcancel_urlthat are used to redirect to in a browser when user finishes
the annotation.
return_url
cancel_url
The URL contains security token that is used by embedded Rossum application to access Rossum API.
When the checking of the document has finished, user clicks
ondonebutton and host application is notified about finished annotation throughsaveendpoint of the connector HTTP API. By default, this call is made asynchronously, which
causes a lag (up to a few seconds) between the click ondonebutton and the call tosaveendpoint. However, it is possible to switch the calls to synchronous mode by switching theconnectorasynchronoustoggle tofalse(seeconnectorfor reference).
save
save
connector
asynchronous
false


# API Reference

For introduction to the Rossum API, seeOverview
Most of the API endpoints require user to be authenticated, seeAuthenticationfor details.


## Annotation

Example annotation object

```
{"document":"https://<example>.rossum.app/api/v1/documents/314628","id":314528,"queue":"https://<example>.rossum.app/api/v1/queues/8199","schema":"https://<example>.rossum.app/api/v1/schemas/95","relations":[],"pages":["https://<example>.rossum.app/api/v1/pages/558598"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","rir_poll_id":"54f6b9ecfa751789f71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/314528","content":"https://<example>.rossum.app/api/v1/annotations/314528/content","time_spent":0,"metadata":{},"related_emails":[],"email":"https://<example>.rossum.app/api/v1/emails/96743","automation_blocker":null,"email_thread":"https://<example>.rossum.app/api/v1/email_threads/34567","has_email_thread_with_replies":true,"has_email_thread_with_new_replies":false,"organization":"https://<example>.rossum.app/api/v1/organizations/1","prediction":null,"assignees":[],"labels":[],"training_enabled":true,"einvoice":false}
```

{"document":"https://<example>.rossum.app/api/v1/documents/314628","id":314528,"queue":"https://<example>.rossum.app/api/v1/queues/8199","schema":"https://<example>.rossum.app/api/v1/schemas/95","relations":[],"pages":["https://<example>.rossum.app/api/v1/pages/558598"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","rir_poll_id":"54f6b9ecfa751789f71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/314528","content":"https://<example>.rossum.app/api/v1/annotations/314528/content","time_spent":0,"metadata":{},"related_emails":[],"email":"https://<example>.rossum.app/api/v1/emails/96743","automation_blocker":null,"email_thread":"https://<example>.rossum.app/api/v1/email_threads/34567","has_email_thread_with_replies":true,"has_email_thread_with_new_replies":false,"organization":"https://<example>.rossum.app/api/v1/organizations/1","prediction":null,"assignees":[],"labels":[],"training_enabled":true,"einvoice":false}
An annotation object contains all extracted and verified data related to a
document. Every document belongs to a queue and is related to the schema
object, that defines datapoint types and overall shape of the extracted data.
Commonly you need to use queue theuploadendpoint to create annotations
instances.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the annotationtrueurlURLURL of the annotationtruestatusenumStatus of the document, seeDocument Lifecyclefor list of value.documentURLRelated document.queueURLQueue that annotation belongs to.schemaURLSchema that defines content shape.relationslist[URL](Deprecated) List of relations that annotation belongs to.pageslist[URL]List of rendered pages.truecreatorURLUser that created the annotation.truecreated_atdatetimeTimestamp of object's creation.truemodifierURLUser that last modified the annotation.modified_byURLUser that last modified the annotation.modified_atdatetimeTimestamp of last modification.trueassigned_atdatetimeTimestamp of last assignment to a user or when the annotation was started being annotated.trueconfirmed_atdatetimeTimestamp when the annotation was moved to statusconfirmed.truedeleted_atdatetimeTimestamp when the annotation was moved to statusdeleted.trueexported_atdatetimeTimestamp of finished export.trueexport_failed_atdatetimeTimestamp of failed export.truepurged_atdatetimeTimestamp when was annotation purged.truerejected_atdatetimeTimestamp when the annotation was moved to statusrejected.trueconfirmed_byURLUser that confirmed the annotation.truedeleted_byURLUser that deleted the annotation.trueexported_byURLUser that exported the annotation.truepurged_byURLUser that purged the annotation.truerejected_byURLUser that rejected the annotation.truerir_poll_idstringInternal.messageslist[object][]List of messages from the connector (save).contentURLLink to annotation data (datapoint values), seeAnnotation data.truesuggested_editURLLink to Suggested edit object.truetime_spentfloat0Total time spent while validating the annotation.metadataobject{}Client data.automatedbooleanfalseWhether annotation was automatedrelated_emailslist[URL]List emails related with annotation.trueemailURLRelated email that the annotation was imported by (for annotations imported by email).trueautomation_blockerURLRelated automation blocker object.trueemail_threadURLRelated email thread object.truehas_email_thread_with_repliesboolRelated email thread contains more than oneincomingemail.truehas_email_thread_with_new_repliesboolRelated email thread contains an unreadincomingemail.trueorganizationURLLink to related organization.trueautomatically_rejectedboolRead-only field of automatically_rejected annotationtruepredictionobjectInternal.trueassigneeslist[URL]List of assigned users (only for internal purposes).truelabelslist[URL]List of selected labelstruerestricted_accessboolfalseAccess to annotation is restrictedtruetraining_enabledbooltrueFlag signalling whether the annotation should be used in the training of the instant learning component.einvoiceboolfalseFlag signalling whether the annotation was ingested as an e-invoice.true
confirmed
deleted
rejected
[]
{}
incoming
incoming

```
"messages": [
    {
      "error": "Invalid invoice number format"
    }
  ]
```

messages

```
"messages": [
    {
      "content": "Invalid invoice number format",
      "id": "197467",
      "type": "error"
    }
  ]
```


### Start annotation

Start annotation of object319668
319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/start'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/start'

```
{"annotation":"https://<example>.rossum.app/api/v1/annotations/319668","session_timeout":"01:00:00"}
```

{"annotation":"https://<example>.rossum.app/api/v1/annotations/319668","session_timeout":"01:00:00"}
POST /v1/annotations/{id}/start
POST /v1/annotations/{id}/start
Start reviewing annotation by the calling user. Can be called withstatusespayload to specify allowed statuses for starting annotation.
Returns409 Conflictif annotation fails to be in one of the specified states.
statuses
409 Conflict
AttributeTypeDefaultDescriptionrequiredstatuseslist[str]["to_review", "reviewing", "postponed", "confirmed"]List of allowed states for the starting annotation to be infalse

#### Response

Status:200
200
Returns object withannotationandsession_timeoutkeys.
annotation
session_timeout

### Start embedded annotation

Start embedded annotation of object319668
319668

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"return_url": "https://service.com/return", "cancel_url": "https://service.com/cancel"}'\'https://<example>.rossum.app/api/v1/annotations/319668/start_embedded'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"return_url": "https://service.com/return", "cancel_url": "https://service.com/cancel"}'\'https://<example>.rossum.app/api/v1/annotations/319668/start_embedded'

```
{"url":"https://<example>.rossum.app/embedded/document/319668#authToken=1c50ae8552441a2cda3c360c1e8cb6f2d91b14a9"}
```

{"url":"https://<example>.rossum.app/embedded/document/319668#authToken=1c50ae8552441a2cda3c360c1e8cb6f2d91b14a9"}
POST /v1/annotations/{id}/start_embedded
POST /v1/annotations/{id}/start_embedded
Start embedded annotation.
KeyDescriptionRequiredreturn_urlURL browser is redirected to in case of successful user validationNocancel_urlURL browser is redirected to in case of user canceling the annotationNopostpone_urlURL browser is redirected to in case of user postponing the annotationNodelete_urlURL browser is redirected to in case of user deleting the annotationNomax_token_lifetime_sDuration (in seconds) for which the token will be valid (default:queue'ssession_timeout, max: 162 hours)No
session_timeout
Embedded annotation cannot be started by users with admin or organization group admin roles.
We strongly recommend starting embedded annotations by users withannotator_embeddeduser roleand permissions for the given queue only to limit the scope of actions that user is able to perform to required minimum.
annotator_embedded

#### Response

Status:200
200
Returns object withurlthat specifies URL to be used in the browser
iframe/popup window. URL includes a token that is valid for this document only
for a limited period of time.
url

### Create embedded URL for annotation

Create embedded URL for annotation object319668
319668

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"return_url": "https://service.com/return", "cancel_url": "https://service.com/cancel"}'\'https://<example>.rossum.app/api/v1/annotations/319668/create_embedded_url'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"return_url": "https://service.com/return", "cancel_url": "https://service.com/cancel"}'\'https://<example>.rossum.app/api/v1/annotations/319668/create_embedded_url'

```
{"url":"https://<example>.rossum.app/embedded/document/319668#authToken=1c50ae8552441a2cda3c360c1e8cb6f2d91b14a9","status":"exported"}
```

{"url":"https://<example>.rossum.app/embedded/document/319668#authToken=1c50ae8552441a2cda3c360c1e8cb6f2d91b14a9","status":"exported"}
POST /v1/annotations/{id}/create_embedded_url
POST /v1/annotations/{id}/create_embedded_url
Similar tostart embedded annotationendpoint but can be called for annotations with all statuses and does not switch status.
KeyDescriptionRequiredreturn_urlURL browser is redirected to in case of successful user validationNocancel_urlURL browser is redirected to in case of user canceling the annotationNopostpone_urlURL browser is redirected to in case of user postponing the annotationNodelete_urlURL browser is redirected to in case of user deleting the annotationNomax_token_lifetime_sDuration (in seconds) for which the token will be valid (default:queue'ssession_timeout, max: 162 hours)No
session_timeout
Embedded annotation cannot be started by users with admin or organization group admin roles.
We strongly recommend creating embedded URLs by users withannotator_embeddeduser roleand permissions for the given queue only to limit the scope of actions that user is able to perform to required minimum.
annotator_embedded

#### Response

Status:200
200
KeyTypeDescriptionurlstrURL to be used in the browser iframe/popup window. URL includes a token that is valid for this document only for a limited period of time.statusenumStatus of annotation, seeannotation lifecycle.

### Confirm annotation

Confirm annotation of object319668
319668
KeyDefaultDescriptionRequiredskip_workflowsFalseWhether to skip workflows evaluation. Read more about workflowshere.bypass_workflows_allowedmust be set totrueinworkflows queue settingsin order to use this featureNo
bypass_workflows_allowed
true

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/confirm'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/confirm'
POST /v1/annotations/{id}/confirm
POST /v1/annotations/{id}/confirm
Confirm annotation, switch status toexported(orexporting).
If theconfirmedstate is enabled, this call moves the annotation
to theconfirmedstatus.
exported
exporting
confirmed
confirmed
Confirm annotation can optionally accept time spent data as described inannotation time spent, for internal use only.
confirmed
exported
confirmed
exported

#### Response

Status:204
204

### Cancel annotation

Cancel annotation of object319668
319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/cancel'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/cancel'
POST /v1/annotations/{id}/cancel
POST /v1/annotations/{id}/cancel
Cancel annotation, switch its status back toto_revieworpostponed.
to_review
postponed
Cancel annotation can optionally accept time spent data as described inannotation time spent, for internal use only.
exporting
exported

#### Response

Status:204
204

### Approve annotation

Approve annotation of object319668
319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{}'\'https://<example>.rossum.app/api/v1/annotations/319668/approve'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{}'\'https://<example>.rossum.app/api/v1/annotations/319668/approve'
POST /v1/annotations/{id}/approve
POST /v1/annotations/{id}/approve
Approve annotation, switch its status toexportingorconfirmed, or it stays inin_workflow, depending on the evaluation of the currentworkflow step
exporting
confirmed
in_workflow
in_workflow
Only admin, organization group admin, or an assigned user with approver role can approve annotation in this state. Aworkflow activityrecord object will be created.

#### Response

Status:200
200
KeyTypeDescriptionstatusstringNew status of the annotation

### Assign annotation

Assign annotation319668to the user1122
319668
1122

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/319668", \
  "assignees": ["https://<example>.rossum.app/api/v1/users/1122"], \
  "note_content": "I just want to reassign as I do not care about it"]}'\'https://<example>.rossum.app/api/v1/annotations/assing'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/319668", \
  "assignees": ["https://<example>.rossum.app/api/v1/users/1122"], \
  "note_content": "I just want to reassign as I do not care about it"]}'\'https://<example>.rossum.app/api/v1/annotations/assing'
POST /v1/annotations/assign
POST /v1/annotations/assign
Changeassigneesof the annotation.
assignees
KeyTypeDescriptionRequiredDefaultannotationslist[URL]List of annotations to change the assignees of (currenlty we support only one annotation at a time)yesassigneeslist[URL]List of users to be added as annotation assigneesyesnote_contentstringContent of the note that will be added to theworkflow activityof actionreassign(only applicable for annotation inin_workflowstate)no""
reassign
in_workflow
""
admin
organization_group_admin

#### Response

Status:204
204

### Reject annotation

Reject annotation of object319668
319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"note_content": "Rejected due to invalid due date."}'\'https://<example>.rossum.app/api/v1/annotations/319668/reject'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"note_content": "Rejected due to invalid due date."}'\'https://<example>.rossum.app/api/v1/annotations/319668/reject'
POST /v1/annotations/{id}/reject
POST /v1/annotations/{id}/reject
Reject annotation, switch its status torejected.
rejected
KeyDescriptionRequiredDefaultnote_contentRejection noteNo""automatically_rejectedFor internal use only (designates whether annotation is displayed as automatically rejected) in the statisticsNofalse
false
to_review
reviewing
postponed
in_workflow
Reject annotation can optionally accept time spent data as described inannotation time spent, for internal use only.
If rejecting inin_workflowstate, theannotation.workflow_run.workflow_statuswill also be set torejectedand aworkflow activityrecord object will be created. Only admin, organization group admin, or an assigned user can approve annotation in this state.
in_workflow
annotation.workflow_run.workflow_status
rejected

#### Response

Status:200
200
KeyTypeDescriptionstatusstringNew status of the annotation (rejected).noteURLLink to Note object.

### Switch to postponed

Postpone annotation status of object319668topostponed
319668
postponed

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/postpone'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/postpone'
POST /v1/annotations/{id}/postpone
POST /v1/annotations/{id}/postpone
Switch annotation status topostpone.
postpone
Postpone annotation can optionally accept time spent data as described inannotation time spent, for internal use only.

#### Response

Status:204
204

### Switch to deleted

Switch annotation status of object319668todeleted
319668
deleted

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/delete'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/delete'
POST /v1/annotations/{id}/delete
POST /v1/annotations/{id}/delete
Switch annotation status todeleted. Annotation with statusdeletedis still available in Rossum UI.
deleted
deleted
Delete annotation can optionally accept time spent data as described inannotation time spent, for internal use only.

#### Response

Status:204
204

### Rotate the annotation

Rotate the annotation319668
319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"rotation_deg": 270}'\'https://<example>.rossum.app/api/v1/annotations/319668/rotate"
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"rotation_deg": 270}'\'https://<example>.rossum.app/api/v1/annotations/319668/rotate"
POST /v1/annotations/{id}/rotate
POST /v1/annotations/{id}/rotate
Rotate a document. It requires one parameter:rotation_deg.
rotation_deg
Status of the annotation is switched toimportingand the extraction phase begins over again.
After the new extraction, the value fromrotation_degfield is copied to pages rotation fieldrotation_deg.
importing
rotation_deg
rotation_deg
KeyDescriptionrotation_degStates degrees by which the document shall be rotated. Possible values: 0, 90, 180, 270.

#### Response

Status:204
204

### Edit the annotation

Edit the annotation319668
319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/1", "rotation_deg": 90}, {"page": "https://<example>.rossum.app/api/v1/pages/2", "rotation_deg": 90}], "metadata": {"document": {"my_info": "something I want to store here"}, "annotation": {"some_key": "some value"}}}, {"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/2", "rotation_deg": 180}]}]}'\'https://<example>.rossum.app/api/v1/annotations/319668/edit"
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/1", "rotation_deg": 90}, {"page": "https://<example>.rossum.app/api/v1/pages/2", "rotation_deg": 90}], "metadata": {"document": {"my_info": "something I want to store here"}, "annotation": {"some_key": "some value"}}}, {"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/2", "rotation_deg": 180}]}]}'\'https://<example>.rossum.app/api/v1/annotations/319668/edit"

```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/documents/320221"},{"document":"https://<example>.rossum.app/api/v1/documents/320552","annotation":"https://<example>.rossum.app/api/v1/documents/320222"}]}
```

{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/documents/320221"},{"document":"https://<example>.rossum.app/api/v1/documents/320552","annotation":"https://<example>.rossum.app/api/v1/documents/320222"}]}
POST /v1/annotations/{id}/editTo edit an annotation from webhook listening toannotation_status.initializeevent and action,
always usesplit endpointinstead.
POST /v1/annotations/{id}/edit
annotation_status.initialize
Edit a document. It requires parameterdocumentsthat contains description of requested edits for annotations that should be
created from the original annotation. Description of each edit contains list of pages and rotation degree.
documents
If used on an annotation in a way that after the editing only one document remains,
the original annotation will be edited. If multiple documents are to be created
after the call, status of the original annotation is switched tosplit,
status of the newly created annotations isimportingand the
extraction phase begins over again. To split the annotation into multiple
annotations, consider using the latest dedicatedsplit endpointinstead.
split
importing
KeyDescriptiondocumentsDocuments that should be created from the original annotation. Each document contains list of pages and rotation degree.
Thedocumentsobject consists of following available parameters:
documents
KeyTypeDescriptionpageslist[object]A list of objects containing information aboutpage(URL) androtation_deg(integer)metadataobject(optional) A dictionary with attributesdocumentandannotationfor adding/updating metadata of edited annotation and its related document.
page
rotation_deg
document
annotation

#### Response

Status:200
200
Returnsresultswith a list of objects:
results
KeyTypeDescriptiondocumentURLURL to the document that was newly created after calling theeditendpoint.annotationURLURL of the annotation assigned to the document.
edit

### Split the annotation

Split the annotation319668
319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/1", "rotation_deg": 90}, {"page": "https://<example>.rossum.app/api/v1/pages/2", "rotation_deg": 90}], "metadata": {"document": {"my_info": "something I want to store here"}, "annotation": {"some_key": "some value"}}}]}'\'https://<example>.rossum.app/api/v1/annotations/319668/split"
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/1", "rotation_deg": 90}, {"page": "https://<example>.rossum.app/api/v1/pages/2", "rotation_deg": 90}], "metadata": {"document": {"my_info": "something I want to store here"}, "annotation": {"some_key": "some value"}}}]}'\'https://<example>.rossum.app/api/v1/annotations/319668/split"

```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/documents/320221"}]}
```

{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/documents/320221"}]}
POST /v1/annotations/{id}/split
POST /v1/annotations/{id}/split
Split a document based on editing rules. It requires parameterdocumentsthat contains description of requested edits for annotations that should be
created from the original annotation. Description of each edit contains list of pages and rotation degree.
documents
When using this endpoint, status of the original annotation is switched tosplit,
status of the newly created annotations isimportingand the
extraction phase begins over again.
split
importing
This endpoint can be used for splitting annotations also from webhook listening toannotation_content.initializeevent and action.
annotation_content.initialize
KeyDescriptiondocumentsDocuments that should be created from the original annotation. Each document contains list of pages and rotation degree.
Thedocumentsobject consists of following available parameters:
documents
KeyTypeDescriptionpageslist[object]A list of objects containing information aboutpage(URL) androtation_deg(integer)metadataobject(optional) A dictionary with attributesdocumentandannotationfor adding/updating metadata of edited annotation and its related document.
page
rotation_deg
document
annotation
Edit annotation can optionally accept time spent data as described inannotation time spent, for internal use only.

#### Response

Status:200
200
Returnsresultswith a list of objects:
results
KeyTypeDescriptiondocumentURLURL to the document that was newly created after calling theeditendpoint.annotationURLURL of the annotation assigned to the document.
edit

### Edit pages Start

Start splitting the document and all its child documents.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages/start'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages/start'

```
{"parent_annotation":"http://<example>.rossum.app/api/v1/annotations/111","children":[{"url":"http://<example>.rossum.app/api/v1/annotations/120","queue":"http://<example>.rossum.app/api/v1/queues/1","status":"reviewing","started":true,"original_file_name":"large_4.pdf","parent_pages":[{"page":"http://<example>.rossum.app/api/v1/pages/142","rotation_deg":0},{"page":"http://<example>.rossum.app/api/v1/pages/143","rotation_deg":0,"deleted":true},{"page":"http://<example>.rossum.app/api/v1/pages/144","rotation_deg":0}],"values":{}},{"url":"http://<example>.rossum.app/api/v1/annotations/119","queue":"http://<example>.rossum.app/api/v1/queues/1","status":"reviewing","started":true,"original_file_name":"large_3.pdf","parent_pages":[{"page":"http://<example>.rossum.app/api/v1/pages/139","rotation_deg":0},{"page":"http://<example>.rossum.app/api/v1/pages/140","rotation_deg":0,"deleted":true},{"page":"http://<example>.rossum.app/api/v1/pages/141","rotation_deg":0}],"values":{}},{"url":null,"queue":"http://<example>.rossum.app/api/v1/queues/23","status":null,"started":false,"original_file_name":"deleted_section.pdf","parent_pages":[{"page":"http://<example>.rossum.app/api/v1/pages/145","rotation_deg":0,"deleted":true},{"page":"http://<example>.rossum.app/api/v1/pages/146","rotation_deg":90,"deleted":true}],"values":{"edit:language":"eng"}}],"session_timeout":"01:00:00"}
```

{"parent_annotation":"http://<example>.rossum.app/api/v1/annotations/111","children":[{"url":"http://<example>.rossum.app/api/v1/annotations/120","queue":"http://<example>.rossum.app/api/v1/queues/1","status":"reviewing","started":true,"original_file_name":"large_4.pdf","parent_pages":[{"page":"http://<example>.rossum.app/api/v1/pages/142","rotation_deg":0},{"page":"http://<example>.rossum.app/api/v1/pages/143","rotation_deg":0,"deleted":true},{"page":"http://<example>.rossum.app/api/v1/pages/144","rotation_deg":0}],"values":{}},{"url":"http://<example>.rossum.app/api/v1/annotations/119","queue":"http://<example>.rossum.app/api/v1/queues/1","status":"reviewing","started":true,"original_file_name":"large_3.pdf","parent_pages":[{"page":"http://<example>.rossum.app/api/v1/pages/139","rotation_deg":0},{"page":"http://<example>.rossum.app/api/v1/pages/140","rotation_deg":0,"deleted":true},{"page":"http://<example>.rossum.app/api/v1/pages/141","rotation_deg":0}],"values":{}},{"url":null,"queue":"http://<example>.rossum.app/api/v1/queues/23","status":null,"started":false,"original_file_name":"deleted_section.pdf","parent_pages":[{"page":"http://<example>.rossum.app/api/v1/pages/145","rotation_deg":0,"deleted":true},{"page":"http://<example>.rossum.app/api/v1/pages/146","rotation_deg":90,"deleted":true}],"values":{"edit:language":"eng"}}],"session_timeout":"01:00:00"}
POST /v1/annotations/{id}/edit_pages/start
POST /v1/annotations/{id}/edit_pages/start
Starts editing the annotation and all its child documents (the documents into which the original document was split). The parent annotation must be in theto_review,splitorreviewingstate (for the calling user).
This call will "lock" the parent and child annotations from being edited. It returns some basic information about the parent annotation and a list of its children. Children to which the current user does not have rights contains only limited information.
If the parent annotation cannot be "locked", an error is returned. If the child annotation cannot be locked, it is skipped and sent in a response with valuestarted=False.
to_review
split
reviewing
started

#### Response

Status:200
200
Returns object with following keys.
KeyTypeDescriptionparent_annotationURLURL of annotationchildrenlist[object]List of child annotation objectssession_timeoutstringtimeout in format "HH:MM:SS"
Thechildrenmember object has following keys:
children
KeyTypeDescriptionurlURLURL of the annotationqueueURLURL of the queuestatusstringStatus of the parent annotationstartedbooleanwas annotation started or notoriginal_file_namestringFile name of original documentparent_pageslist[object]List of annotation pages from parent document with its rotation.valuesobjectEdit valuesto be propagated to newly created annotations. Keys must be prefixed with "edit:", e.g. "edit:document_type".Schema Datapoint descriptiondescribes how it is used to initialize datapoint value.
Theparent_pagesmember object has following keys:
parent_pages
KeyTypeDescriptionpageURLURL of annotationrotation_degintegerRotation in degreesdeletedbooleanIndicates whether the page is marked as deleted.
Status:403
403
User doesn't have a right to edit parent annotation.

### Edit pages Cancel

Cancel splitting the document and its child documents.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages/cancel'-d\'{"annotations": ["http://<example>.rossum.app/api/v1/annotations/119"], "cancel_parent": false, "processing_duration": {"time_spent": 10.0}}'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages/cancel'-d\'{"annotations": ["http://<example>.rossum.app/api/v1/annotations/119"], "cancel_parent": false, "processing_duration": {"time_spent": 10.0}}'
POST /v1/annotations/{id}/edit_pages/cancel
POST /v1/annotations/{id}/edit_pages/cancel
Cancel multiple started child annotations at once. By default cancel also parent annotation (optional).
KeyTypeDescriptionannotationslist[URL]List of urls of child annotations to cancel. Must be inreviewingstate.cancel_parentbooleanCancel parent annotation. Optional, default true.processing_durationobjectOptionalprocessing_durationobject
reviewing

#### Response

Status:204on success.
204
Status:400when preconditions are not met.
400

### Edit pages

Split the document and move one of the new child documents into different queue.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"edit": [{"parent_pages": [{"page": "http://<example>.rossum.app/api/v1/pages/142", "rotation_deg": 90}], "values": {"edit:some_key": "some value"}},{"parent_pages": [{"page": "http://<example>.rossum.app/api/v1/pages/141", "rotation_deg": 90}], "target_queue": "https://<example>.rossum.app/api/v1/queues/23"}], "stop_parent": true}'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"edit": [{"parent_pages": [{"page": "http://<example>.rossum.app/api/v1/pages/142", "rotation_deg": 90}], "values": {"edit:some_key": "some value"}},{"parent_pages": [{"page": "http://<example>.rossum.app/api/v1/pages/141", "rotation_deg": 90}], "target_queue": "https://<example>.rossum.app/api/v1/queues/23"}], "stop_parent": true}'

```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/annotations/320221"},{"document":"https://<example>.rossum.app/api/v1/documents/320552","annotation":"https://<example>.rossum.app/api/v1/annotations/320222"}]}
```

{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/annotations/320221"},{"document":"https://<example>.rossum.app/api/v1/documents/320552","annotation":"https://<example>.rossum.app/api/v1/annotations/320222"}]}
Join of two child documents (784, 785, each with one page) into single new document.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"edit": [{"parent_pages": [{"page":"https://<example>.rossum.app/api/v1/pages/1088", "rotation_deg": 0}, {"page": "https://<example>.rossum.app/api/v1/pages/1089", "rotation_deg": 0}], "document_name": "joined_pages.pdf"}],"delete": ["https://<example>.rossum.app/api/v1/annotations/784", "https://<example>.rossum.app/api/v1/annotations/785"]}'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"edit": [{"parent_pages": [{"page":"https://<example>.rossum.app/api/v1/pages/1088", "rotation_deg": 0}, {"page": "https://<example>.rossum.app/api/v1/pages/1089", "rotation_deg": 0}], "document_name": "joined_pages.pdf"}],"delete": ["https://<example>.rossum.app/api/v1/annotations/784", "https://<example>.rossum.app/api/v1/annotations/785"]}'

```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/annotations/786"}]}
```

{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/annotations/786"}]}
Move one child document into different queue.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"move": [{"annotation": "https://<example>.rossum.app/api/v1/annotations/784", "target_queue": "https://<example>.rossum.app/api/v1/queues/23"}]}'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"move": [{"annotation": "https://<example>.rossum.app/api/v1/annotations/784", "target_queue": "https://<example>.rossum.app/api/v1/queues/23"}]}'

```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/annotations/784"}]}
```

{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/annotations/784"}]}
Delete one child document.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"delete": ["https://<example>.rossum.app/api/v1/annotations/784"]}'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"delete": ["https://<example>.rossum.app/api/v1/annotations/784"]}'

```
{"results":[]}
```

{"results":[]}
POST /v1/annotations/{parent_id}/edit_pages
POST /v1/annotations/{parent_id}/edit_pages
Edit document pages, split and re-split already split document.
When using this endpoint, status of the original annotation (when not editing existing split) is switched tosplit,
status of the newly created annotations isimportingand the
extraction phase begins over again.
split
importing
This endpoint can be used for splitting annotations also from webhook listening toannotation_content.initializeevent and action.
annotation_content.initialize
KeyTypeDescriptiondeletelist[URL]Optional list of urls of child annotations to delete.movelist[object]Optional list of Move objects.editlist[object]Optional list of Edit objects.stop_reviewinglist[URL]Optional list of urls of child annotations to stop reviewing. Must be inreviewingstate.stop_parentbooleanStop also parent annotation. Optional, default true.edit_data_sourceStringOptional source of edit data. Eitherautomation,suggest,modified_suggestormanual.processing_durationobjectOptionalprocessing_durationobject.
reviewing
automation
suggest
modified_suggest
manual
TheMove objecthas the following keys:
Move object
KeyTypeDescriptionannotationURLURL of annotation.target_queueURLURL of target queue.
TheEdit objecthas the following keys:
Edit object
KeyTypeDescriptionannotationURLOptional URL of annotation.target_queueURLOptional URL of target queue.document_nameStringOptional document name. When not provided, generated automatically.parent_pageslist[object]List of parent pages with rotation.metadataobjectMetadata object. May contain objectsannotationandmetadatawhich are saved in created/edited annotation/document metadata.valuesobjectValues to be propagated to newly created annotations. Keys must be prefixed with "edit:", e.g. "edit:document_type".
annotation
metadata
TheParent pageobject has the following keys:
Parent page
KeyTypeDescriptionRequiredDefault valuepageURLURL of page.yesrotation_degintRotation angle in degrees with a step of 90 degreesno0deletedbooleanIndicates whether the page is marked as deleted.nofalse
0
false

#### Response

Status:200on success.
200
Returnsresultswith a list of objects:
results
KeyTypeDescriptiondocumentURLURL to the document that was newly created after calling theeditendpoint.annotationURLURL of the annotation assigned to the document.
edit
Status:400when preconditions are not met.
400

### Edit pages in-place

Edit pages of document and move to different queue.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages/in_place'-d\'{"parent_pages": [{"page": "http://<example>.rossum.app/api/v1/pages/142", "rotation_deg": 90}], "target_queue": "https://<example>.rossum.app/api/v1/queues/23"}'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages/in_place'-d\'{"parent_pages": [{"page": "http://<example>.rossum.app/api/v1/pages/142", "rotation_deg": 90}], "target_queue": "https://<example>.rossum.app/api/v1/queues/23"}'

```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/2121","annotation":"https://<example>.rossum.app/api/v1/annotations/111"}]}
```

{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/2121","annotation":"https://<example>.rossum.app/api/v1/annotations/111"}]}
POST /v1/annotations/{parent_id}/edit_pages/in_place
POST /v1/annotations/{parent_id}/edit_pages/in_place
Edit existing document pages without creating new annotations. You can rotate pages, delete pages or move the annotation into another queue.
This endpoint can be used for the embedded mode.
KeyTypeDescriptionparent_pageslist[object]List of parent pages with rotation.target_queueURLOptional URL of target queue.metadataobjectOptional metadata object. May contain objectsannotationandmetadatawhich are saved in created/edited annotation/document metadata.edit_data_sourceStringOptional source of edit data. Eitherautomation,suggest,modified_suggestormanual.processing_durationobjectOptionalprocessing_durationobject.
annotation
metadata
automation
suggest
modified_suggest
manual
TheParent pageobject has the following keys:
Parent page
KeyTypeDescriptionpageURLURL of page.rotation_degintRotation angle in deg. with step 90 deg.deletedbooleanIndicates whether the page is marked as deleted.

#### Response

Status:200on success.
200
Returnsresultswith a list of objects:
results
KeyTypeDescriptiondocumentURLURL to the document that was newly created after calling theeditendpoint.annotationURLURL of the annotation assigned to the document.
edit
Status:400when preconditions are not met.
400

### Search for text

Search for text in annotation319668
319668

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/search?phrase=some'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/search?phrase=some'

```
{"results":[{"rectangle":[67.15157010915198,545.9286363906203,87.99106633081445,563.4617583852776],"page":1},{"rectangle":[45.27717884130982,1060.3084761056693,66.11667506297229,1077.8415981003266],"page":1}],"status":"ok"}
```

{"results":[{"rectangle":[67.15157010915198,545.9286363906203,87.99106633081445,563.4617583852776],"page":1},{"rectangle":[45.27717884130982,1060.3084761056693,66.11667506297229,1077.8415981003266],"page":1}],"status":"ok"}
GET /v1/annotations/{id}/search
GET /v1/annotations/{id}/search
Search for a phrase in the document.
ArgumentTypeDescriptionphrasestringA phrase to search fortoleranceintegerAllowedEdit distancefrom the search phrase (number of removal, insertion or substitution operations that need to be performed for strings to match). Only used for OCR invoices (images, such as png or PDF with scanned images). Default value is computed aslength(phrase)/4.
length(phrase)/4

#### Response

Status:200
200
Returnsresultswith a list of objects:
results
KeyTypeDescriptionrectanglelist[float]Bounding box of an occurrence.pageintegerPage of occurrence.

### Search for annotations

Supported ordering:id,arrived_at,assigned_at,assignees,automated,confirmed_at,confirmed_by__username,confirmed_by,created_at,creator__username,creator,deleted_at,deleted_by__username,deleted_by,document,exported_at,exported_by__username,exported_by,export_failed_at,has_email_thread_with_new_replies,has_email_thread_with_replies,labels,modified_at,modifier__username,modifier,original_file_name,purged_at,purged_by__username,purged_by,queue,rejected_at,rejected_by__username,rejected_by,relations__key,relations__parent,relations__type,rir_poll_id,status,workspace,email_thread,email_sender,field.<schema_id>.<format>(whereformatis one ofnumber,date,string).
id
arrived_at
assigned_at
assignees
automated
confirmed_at
confirmed_by__username
confirmed_by
created_at
creator__username
creator
deleted_at
deleted_by__username
deleted_by
document
exported_at
exported_by__username
exported_by
export_failed_at
has_email_thread_with_new_replies
has_email_thread_with_replies
labels
modified_at
modifier__username
modifier
original_file_name
purged_at
purged_by__username
purged_by
queue
rejected_at
rejected_by__username
rejected_by
relations__key
relations__parent
relations__type
rir_poll_id
status
workspace
email_thread
email_sender
field.<schema_id>.<format>
format
number
date
string
Obtain only annotations matching a complex filter

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'\-d'{"query": {"$and": [{"field.vendor_name.string": {"$eq": "ACME corp"}}, {"labels": {"$in": ["https://<example>.rossum.app/api/v1/labels/12", "https://<example>.rossum.app/api/v1/labels/34"]}}]}, "query_string": {"string": "explosives"}}'\'https://<example>.rossum.app/api/v1/annotations/search?ordering=status,confirmed_by__username,field.amount_total.number'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'\-d'{"query": {"$and": [{"field.vendor_name.string": {"$eq": "ACME corp"}}, {"labels": {"$in": ["https://<example>.rossum.app/api/v1/labels/12", "https://<example>.rossum.app/api/v1/labels/34"]}}]}, "query_string": {"string": "explosives"}}'\'https://<example>.rossum.app/api/v1/annotations/search?ordering=status,confirmed_by__username,field.amount_total.number'

```
{"pagination":{"total":101,"total_pages":6,"next":"https://<example>.rossum.app/api/v1/annotations/search?search_after=eyJxdWVyeV9oYXNoIjogImM2ZWIzNjA5MDI1NWNmNTg4ODk0YWE5MGZiMjVmZjBlIiwgInNlYXJjaF9hZnRlciI6IFsxNTg2NTMwMzI0MDAwLCAyXSwgInJldmVyc2VkIjogZmFsc2V9%3A1NYBmgNCV-Ssmf7G9rd9vXnBY-BuvCZWrD95wcb2jIg","previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","document":"https://<example>.rossum.app/api/v1/documents/315877",...}]}
```

{"pagination":{"total":101,"total_pages":6,"next":"https://<example>.rossum.app/api/v1/annotations/search?search_after=eyJxdWVyeV9oYXNoIjogImM2ZWIzNjA5MDI1NWNmNTg4ODk0YWE5MGZiMjVmZjBlIiwgInNlYXJjaF9hZnRlciI6IFsxNTg2NTMwMzI0MDAwLCAyXSwgInJldmVyc2VkIjogZmFsc2V9%3A1NYBmgNCV-Ssmf7G9rd9vXnBY-BuvCZWrD95wcb2jIg","previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","document":"https://<example>.rossum.app/api/v1/documents/315877",...}]}
POST /v1/annotations/search
POST /v1/annotations/search
Search for annotations matching a complex filter
KeyTypeDescriptionqueryobjectA subset of MongoDB Query Language (seequery definitionbelow)query_stringobjectObject with configuration for full-text search (seequery string definitionbelow)
Ifquery_stringis used together withquery, search is done as a conjunction of these expressions
(query_stringANDquery).
query_string
query
query_string
query
A list of definitions under a$andkey:
$and
KeyTypeDescription<meta_field>objectMatches against annotation metadata according to <meta_field>. (Seedefinitionbelow)field.<schema_id>.<type>objectMatches against annotation content value according to <schema_id> treating it as <type>. (Seedefinitionbelow)
field.<schema_id>.typeis of type: string | number | date (in ISO 8601 format). Max. 256 characters long strings are allowed.
field.<schema_id>.type
meta_fieldcan be one of:
meta_field
Meta field nameTypeannotationURLarrived_atdateassigned_atdateassigneesURLautomatedboolautomatically_rejectedboolconfirmed_atdateconfirmed_by__usernamestringconfirmed_byURLcreated_atdatecreator__usernamestringcreatorURLdeleted_atdatedeleted_by__usernamestringdeleted_byURLdocumentURLeinvoiceboolexported_atdateexported_by__usernamestringexported_byURLhas_email_thread_with_new_repliesboolhas_email_thread_with_repliesboollabelsURLmessagesstringmodified_atdatemodifier__usernamestringmodifierURLoriginal_file_namestringpurged_atdatepurged_by__usernamestringpurged_byURLqueueURLrejected_atdaterejected_by__usernamestringrejected_byURLrelations__keystringrelations__parentURLrelations__typestringrestricted_accessboolrir_poll_idstringstatusstringworkspaceURLemail_threadURLemail_senderstring
annotation
arrived_at
assigned_at
assignees
automated
automatically_rejected
confirmed_at
confirmed_by__username
confirmed_by
created_at
creator__username
creator
deleted_at
deleted_by__username
deleted_by
document
einvoice
exported_at
exported_by__username
exported_by
has_email_thread_with_new_replies
has_email_thread_with_replies
labels
messages
modified_at
modifier__username
modifier
original_file_name
purged_at
purged_by__username
purged_by
queue
rejected_at
rejected_by__username
rejected_by
relations__key
relations__parent
relations__type
restricted_access
rir_poll_id
status
workspace
email_thread
email_sender
KeyTypeDescription$startsWithstringMatches the start of a value. Must be at least 2 characters long.$anyTokenStartsWithstringMatches the start of each token within a string. Must be at least 2 characters long.$containsPrefixesstringSame as $anyTokenStartsWith but query is split into tokens (words). Must be at least 2 characters long. Example queryquick brownmatchesquick brown foxbut alsobrown quick dogorquickiest brown fox, but notquick dog.$emptyOrMissingboolMatches values that are empty or missing. Whenfalse, matches existing non-empty values.$eq | $nenumber | string | date | URLDefaultMQL behavior$gt | $lt | $gte | $ltenumber | string | dateDefaultMQL behavior$in | $ninlist[number | string | URL]DefaultMQL behavior
quick brown
quick brown fox
brown quick dog
quickiest brown fox
quick dog
false
Related objects can besideloadedandquery fieldscan be used in the same way as whenlisting annotations.
datapoint
content

#### Response

Status:200
200
Returnspaginatedresponse with a list ofannotationobjects, likeannotations list
Status:410
410
Value ofsearch_afteris not valid anymore. Retry the search with a different value.
search_after
Obtain only annotations matching prefixexplosive
explosive

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'\-d'{"query_string": {"string": "expl"}}'\'https://<example>.rossum.app/api/v1/annotations/search?ordering=status,confirmed_by__username,field.amount_total.number'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'\-d'{"query_string": {"string": "expl"}}'\'https://<example>.rossum.app/api/v1/annotations/search?ordering=status,confirmed_by__username,field.amount_total.number'

```
{"pagination":{"total":101,"total_pages":6,"next":"https://<example>.rossum.app/api/v1/annotations/search?search_after=eyJxdWVyeV9oYXNoIjogImM2ZWIzNjA5MDI1NWNmNTg4ODk0YWE5MGZiMjVmZjBlIiwgInNlYXJjaF9hZnRlciI6IFsxNTg2NTMwMzI0MDAwLCAyXSwgInJldmVyc2VkIjogZmFsc2V9%3A1NYBmgNCV-Ssmf7G9rd9vXnBY-BuvCZWrD95wcb2jIg","previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","document":"https://<example>.rossum.app/api/v1/documents/315877",...}]}
```

{"pagination":{"total":101,"total_pages":6,"next":"https://<example>.rossum.app/api/v1/annotations/search?search_after=eyJxdWVyeV9oYXNoIjogImM2ZWIzNjA5MDI1NWNmNTg4ODk0YWE5MGZiMjVmZjBlIiwgInNlYXJjaF9hZnRlciI6IFsxNTg2NTMwMzI0MDAwLCAyXSwgInJldmVyc2VkIjogZmFsc2V9%3A1NYBmgNCV-Ssmf7G9rd9vXnBY-BuvCZWrD95wcb2jIg","previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","document":"https://<example>.rossum.app/api/v1/documents/315877",...}]}
Apply full-text search to datapoint values using a chosen term. The value is searched by
its prefix, separately for each term separated by whitespace, in case-insensitive way. Special characters
at the end of the strings are ignored. For example, when searching for a termLarge drink, all of the following
values passed would give a match:lar#,lar dri,dri.
We search also in the non-extracted page data, if the data are available.
Large drink
lar#
lar dri
dri
Ifquery_stringis used together withquery, search is done as a conjunction of these expressions
(query_stringANDquery).
query_string
query
query_string
query
KeyTypeDescriptionstringstringString to be used for full-text search. At least 2 characters need to be passed to apply this search. Max. 256 characters long strings are allowed.
Pagination is set by query parameters of the URL. Request body and ordering mustn't be changed when listing through pages, otherwise400response is returned.
400
KeyDefaultTypeDescriptionpage_size20intNumber of results per page. The maximum value is 500 (*)search_afternullstringEncoded value acting as a cursor (do not try to modify, only for internal purposes).
null
(*) For requests that sideloadcontent, the maximum value is limited to 100. Sideloading content for this endpoint is deprecated and
will be removed in the near future.
content

### Convert grid to table data

Convert grid to tabular data in annotation319623
319623

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319623/content/37507202/transform_grid_to_datapoints'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319623/content/37507202/transform_grid_to_datapoints'
POST /v1/annotations/{id}/content/{id of the child node}/transform_grid_to_datapoints
POST /v1/annotations/{id}/content/{id of the child node}/transform_grid_to_datapoints
Transform grid structure to tabular data of related multivalue object.

#### Response

Status:200
200
All tuple datapoints and their children are returned.

### Add new row to multivalue datapoint

Add row to annotation319623multivalue37507202
319623
37507202

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319623/content/37507202/add_empty'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319623/content/37507202/add_empty'
POST /v1/annotations/{id}/content/{id of the child node}/add_empty
POST /v1/annotations/{id}/content/{id of the child node}/add_empty
Adds a row to a multivalue table. This row will not be connected to the grid and modifications of the grid will not trigger any OCR on the cells of this row.

#### Response

Status:200
200

### Validate annotation content

Validate the content of annotation319623
319623

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"updated_datapoint_ids": [37507204]}'\'https://<example>.rossum.app/api/v1/annotations/319623/content/validate'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"updated_datapoint_ids": [37507204]}'\'https://<example>.rossum.app/api/v1/annotations/319623/content/validate'

```
{"messages":[{"id":"1038654","type":"error","content":"required","detail":{"hook_id":"42345","hook_name":"Webhook 8365","request_id":"6166deb3-2f89-4fc2-9359-56cc8e3838e4","is_exception":true,"timestamp":"2022-10-10T15:00:00.000000Z"}},{"id":"all","type":"error","content":"Whole document is invalid.","detail":{"hook_id":"94634","hook_name":"Function 4934","request_id":"5477aeb2-8f43-3fe1-9279-23bc8e4121e5","is_exception":true,"timestamp":"2022-10-10T15:00:00.000000Z"}},{"id":"1038456","type":"aggregation","content":"246.456","aggregation_type":"sum","schema_id":"vat_detail_tax2"}],"updated_datapoints":[{"id":37507205,"url":"https://<example>.rossum.app/api/v1/annotations/319623/content/37507205","content":{"value":"new value","page":1,"position":[0.0,1.0,2.0,3.0],"rir_text":null,"rir_page":null,"rir_position":null,"rir_confidence":null,"connector_position":[0.0,1.0,2.0,3.0],"connector_text":"new value"},"category":"datapoint","schema_id":"vat_rate","validation_sources":["connector","history"],"time_spent":0.0,"time_spent_overall":0.0,"options":[{"value":"value","label":"label"}],"hidden":false}],"suggested_operations":[{"op":"replace","id":"198143","value":{"content":{"value":"John","position":[103,110,121,122],"page":1},"hidden":false,"options":[],"validation_sources":["human"]}},{"op":"remove","id":"884061"}],"matched_trigger_rules":[{"type":"page_count","value":24,"threshold":10},{"type":"filename","value":"spam.pdf","regex":"^spam.*"},{"id":198143,"value":"foobar","type":"datapoint"}]}
```

{"messages":[{"id":"1038654","type":"error","content":"required","detail":{"hook_id":"42345","hook_name":"Webhook 8365","request_id":"6166deb3-2f89-4fc2-9359-56cc8e3838e4","is_exception":true,"timestamp":"2022-10-10T15:00:00.000000Z"}},{"id":"all","type":"error","content":"Whole document is invalid.","detail":{"hook_id":"94634","hook_name":"Function 4934","request_id":"5477aeb2-8f43-3fe1-9279-23bc8e4121e5","is_exception":true,"timestamp":"2022-10-10T15:00:00.000000Z"}},{"id":"1038456","type":"aggregation","content":"246.456","aggregation_type":"sum","schema_id":"vat_detail_tax2"}],"updated_datapoints":[{"id":37507205,"url":"https://<example>.rossum.app/api/v1/annotations/319623/content/37507205","content":{"value":"new value","page":1,"position":[0.0,1.0,2.0,3.0],"rir_text":null,"rir_page":null,"rir_position":null,"rir_confidence":null,"connector_position":[0.0,1.0,2.0,3.0],"connector_text":"new value"},"category":"datapoint","schema_id":"vat_rate","validation_sources":["connector","history"],"time_spent":0.0,"time_spent_overall":0.0,"options":[{"value":"value","label":"label"}],"hidden":false}],"suggested_operations":[{"op":"replace","id":"198143","value":{"content":{"value":"John","position":[103,110,121,122],"page":1},"hidden":false,"options":[],"validation_sources":["human"]}},{"op":"remove","id":"884061"}],"matched_trigger_rules":[{"type":"page_count","value":24,"threshold":10},{"type":"filename","value":"spam.pdf","regex":"^spam.*"},{"id":198143,"value":"foobar","type":"datapoint"}]}
POST /v1/annotations/{id}/content/validate
POST /v1/annotations/{id}/content/validate
Validate the content of an annotation.
At first, the content is sent to thevalidate hookof connected extension.
Then some standard validations (datatype,constraintsare checked) are carried out in Rossum.
Additionally, if the annotation's respective queue has enabled delete recommendation conditions,
they are evaluated as well.
type
constraints
KeyTypeDescriptionactionslist[enum]Validation actions. Possible values :["user_update"],["user_update", "updated"]or["user_update", "started"](default:["user_update"])updated_datapoint_idslist[int]List of IDs of datapoints that were changed since last call ofthis endpoint.
["user_update"]
["user_update", "updated"]
["user_update", "started"]
["user_update"]

#### Response

Status:200
200
KeyTypeDescriptionmessageslist[object]Bounding box of an occurrence.updated_datapointslist[object]Page of occurrence.suggested_operationslist[object]Datapoint operations suggested as a result of validation.matched_trigger_ruleslist[object]Delete Recommendationrules that matched.
By default, messages for hidden datapoints are omitted. The behavior could be changed using themessages_for_hidden_datapoints=truequery parameter.
messages_for_hidden_datapoints=true
The message object contains attributes:
KeyTypeDescriptionidstringID of the concerned datapoint;"all"for a document-wide issuestypeenumOne of:error,warning,infooraggregation.contentstringA message shown in UI. Limited to 4096 characters.detailobjectDetail object that gives more context to the message.aggregation_type (*)enumType of aggregation (currently supported"sum"aggregation type).schema_id (*)stringIdentifier of schema datapoint for which is aggregation computed.
"all"
"sum"
(*) Attribute present only in message with type"aggregation".
"aggregation"
The message detail can contain the following attributes:
KeyTypeDescriptionhook_idintID of the hook,nullfor computed fields.hook_namestringName of the hook.request_idstringID of the request preceding this hook's response.timestampstringTimestamp of the request preceding this hook's response.is_exceptionboolFlag signaling non-200 response from the hook or error during computed field evaluation.traceback_line_numberintLine of the error in the computed field code.source_idintId of the datapoint which created this message.source_schema_idstringSchema id of the datapoint which created this message.
null
The updated datapoint object contains the subtrees ofdatapointsupdated from anextension.
The suggestions follow the same format as the one that can be specified in requests - please refer to theannotation dataAPI for a complete description.
The base of the response looks like this, the remaining fields depend on the "type" field and are
prone to change.
KeyTypeDescriptiontypestringOne of "page_count", "filename", "datapoint".

### List all annotations

List all annotations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations'

```
{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/31336","pages":["https://<example>.rossum.app/api/v1/pages/561206"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","rir_poll_id":"54f6b9ecfa751789f71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},...},{...}]}
```

{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/31336","pages":["https://<example>.rossum.app/api/v1/pages/561206"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","rir_poll_id":"54f6b9ecfa751789f71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},...},{...}]}
GET /v1/annotations
GET /v1/annotations
Retrieve all annotation objects.
Supported ordering:document,document__arrived_at,document__original_file_name,modifier,modifier__username,modified_by,modified_by__username,creator,creator__username,queue,status,created_at,assigned_at,confirmed_at,modified_at,exported_at,export_failed_at,purged_at,rejected_at,deleted_at,confirmed_by,deleted_by,exported_by,purged_by,rejected_by,confirmed_by__username,deleted_by__username,exported_by__username,purged_by__username,rejected_by__username
document
document__arrived_at
document__original_file_name
modifier
modifier__username
modified_by
modified_by__username
creator
creator__username
queue
status
created_at
assigned_at
confirmed_at
modified_at
exported_at
export_failed_at
purged_at
rejected_at
deleted_at
confirmed_by
deleted_by
exported_by
purged_by
rejected_by
confirmed_by__username
deleted_by__username
exported_by__username
purged_by__username
rejected_by__username

#### Filters

Obtain only annotations with parent annotation 1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?relations__parent=1500'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?relations__parent=1500'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/2","id":2,"queue":"https://<example>.rossum.app/api/v1/queues/1","schema":"https://<example>.rossum.app/api/v1/schemas/1","relations":["https://<example>.rossum.app/api/v1/relations/1"],..."url":"https://<example>.rossum.app/api/v1/annotations/2",...},{"document":"https://<example>.rossum.app/api/v1/documents/3","id":3,"queue":"https://<example>.rossum.app/api/v1/queues/2","schema":"https://<example>.rossum.app/api/v1/schemas/2","relations":["https://<example>.rossum.app/api/v1/relations/1"],..."url":"https://<example>.rossum.app/api/v1/annotations/3",...}]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/2","id":2,"queue":"https://<example>.rossum.app/api/v1/queues/1","schema":"https://<example>.rossum.app/api/v1/schemas/1","relations":["https://<example>.rossum.app/api/v1/relations/1"],..."url":"https://<example>.rossum.app/api/v1/annotations/2",...},{"document":"https://<example>.rossum.app/api/v1/documents/3","id":3,"queue":"https://<example>.rossum.app/api/v1/queues/2","schema":"https://<example>.rossum.app/api/v1/schemas/2","relations":["https://<example>.rossum.app/api/v1/relations/1"],..."url":"https://<example>.rossum.app/api/v1/annotations/3",...}]}
Filters may be specified to limit annotations to be listed.
AttributeDescriptionstatusAnnotationstatus, multiple values may be separated using a commaidList of ids separated by a commamodifierUser idconfirmed_byUser iddeleted_byUser idexported_byUser idpurged_byUser idrejected_byUser idassigneesUser id, multiple values may be separated using a commalabelsLabel id, multiple values may be separated using a commadocumentDocument idqueueList of queue ids separated by a commaqueue__workspaceList of workspace ids separated by a commarelations__parentID of parent annotation defined in relatedRelationobjectrelations__typeType ofRelationthat annotation belongs torelations__keyKey ofRelationthat annotation belongs toarrived_at_beforeISO 8601 timestamp (e.g.arrived_at_before=2019-11-15)arrived_at_afterISO 8601 timestamp (e.g.arrived_at_after=2019-11-14)assigned_at_beforeISO 8601 timestamp (e.g.assigned_at_before=2019-11-15)assigned_at_afterISO 8601 timestamp (e.g.assigned_at_after=2019-11-14)confirmed_at_beforeISO 8601 timestamp (e.g.confirmed_at_before=2019-11-15)confirmed_at_afterISO 8601 timestamp (e.g.confirmed_at_after=2019-11-14)modified_at_beforeISO 8601 timestamp (e.g.modified_at_before=2019-11-15)modified_at_afterISO 8601 timestamp (e.g.modified_at_after=2019-11-14)deleted_at_beforeISO 8601 timestamp (e.g.deleted_at_before=2019-11-15)deleted_at_afterISO 8601 timestamp (e.g.deleted_at_after=2019-11-14)exported_at_beforeISO 8601 timestamp (e.g.exported_at_before=2019-11-14 22:00:00)exported_at_afterISO 8601 timestamp (e.g.exported_at_after=2019-11-14 12:00:00)export_failed_at_beforeISO 8601 timestamp (e.g.export_failed_at_before=2019-11-14 22:00:00)export_failed_at_afterISO 8601 timestamp (e.g.export_failed_at_after=2019-11-14 12:00:00)purged_at_beforeISO 8601 timestamp (e.g.purged_at_before=2019-11-15)purged_at_afterISO 8601 timestamp (e.g.purged_at_after=2019-11-14)rejected_at_beforeISO 8601 timestamp (e.g.rejected_at_before=2019-11-15)rejected_at_afterISO 8601 timestamp (e.g.rejected_at_after=2019-11-14)restricted_accessBooleanautomatedBooleanhas_email_thread_with_repliesBoolean (related email thread contains more than oneincomingemails)has_email_thread_with_new_repliesBoolean (related email thread contains unreadincomingemail)searchString, seeAnnotation search
arrived_at_before=2019-11-15
arrived_at_after=2019-11-14
assigned_at_before=2019-11-15
assigned_at_after=2019-11-14
confirmed_at_before=2019-11-15
confirmed_at_after=2019-11-14
modified_at_before=2019-11-15
modified_at_after=2019-11-14
deleted_at_before=2019-11-15
deleted_at_after=2019-11-14
exported_at_before=2019-11-14 22:00:00
exported_at_after=2019-11-14 12:00:00
export_failed_at_before=2019-11-14 22:00:00
export_failed_at_after=2019-11-14 12:00:00
purged_at_before=2019-11-15
purged_at_after=2019-11-14
rejected_at_before=2019-11-15
rejected_at_after=2019-11-14
incoming
incoming
If this filter is used, annotations are filtered based on full-text search in annotation's datapoint values, original
file name, modifier user email and messages. Max. 256 characters allowed.

#### Query fields

Obtain only subset of annotation attributes

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?fields=id,url'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?fields=id,url'

```
{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"id":320332,"url":"https://<example>.rossum.app/api/v1/annotations/320332"},{"id":319668,"url":"https://<example>.rossum.app/api/v1/annotations/319668"},...]}
```

{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"id":320332,"url":"https://<example>.rossum.app/api/v1/annotations/320332"},{"id":319668,"url":"https://<example>.rossum.app/api/v1/annotations/319668"},...]}
In order to obtain only subset of annotation object attributes, one can use query parameterfields.
fields
ArgumentDescriptionfieldsComma-separated list of attributes to beincludedin the response.fields!Comma-separated list of attributes to beexcludedfrom the response.

#### Sideloading

Sideload documents, modifiers and content

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?sideload=modifiers,documents,content&content.schema_id=item_amount_total'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?sideload=modifiers,documents,content&content.schema_id=item_amount_total'

```
{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320432","id":320332,...,"modifier":"https://<example>.rossum.app/api/v1/users/10775","status":"to_review","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/320332","content":"https://<example>.rossum.app/api/v1/annotations/320332/content","time_spent":0,"metadata":{}},...],"documents":[{"id":320432,"url":"https://<example>.rossum.app/api/v1/documents/320432",...},...],"modifiers":[{"id":10775,"url":"https://<example>.rossum.app/api/v1/users/10775",...},...],"content":[{"id":19434,"url":"https://<example>.rossum.app/api/v1/annotations/320332/content/19434","category":"datapoint","schema_id":"item_amount_total",...}...]}
```

{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320432","id":320332,...,"modifier":"https://<example>.rossum.app/api/v1/users/10775","status":"to_review","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/320332","content":"https://<example>.rossum.app/api/v1/annotations/320332/content","time_spent":0,"metadata":{}},...],"documents":[{"id":320432,"url":"https://<example>.rossum.app/api/v1/documents/320432",...},...],"modifiers":[{"id":10775,"url":"https://<example>.rossum.app/api/v1/users/10775",...},...],"content":[{"id":19434,"url":"https://<example>.rossum.app/api/v1/annotations/320332/content/19434","category":"datapoint","schema_id":"item_amount_total",...}...]}
Sideload content filtered by schema_id

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?sideload=content&content.schema_id=sender_id,vat_detail_tax'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?sideload=content&content.schema_id=sender_id,vat_detail_tax'

```
{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320432","id":320332,...,"modifier":"https://<example>.rossum.app/api/v1/users/10775","status":"to_review","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/320332","content":"https://<example>.rossum.app/api/v1/annotations/320332/content","time_spent":0,"metadata":{}},...],"content":[{"id":15984,"url":"https://<example>.rossum.app/api/v1/annotations/320332/content/15984","category":"datapoint","schema_id":"sender_id",...},{"id":15985,"url":"https://<example>.rossum.app/api/v1/annotations/320332/content/15985","category":"datapoint","schema_id":"vat_detail_tax",...},...]}
```

{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320432","id":320332,...,"modifier":"https://<example>.rossum.app/api/v1/users/10775","status":"to_review","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/320332","content":"https://<example>.rossum.app/api/v1/annotations/320332/content","time_spent":0,"metadata":{}},...],"content":[{"id":15984,"url":"https://<example>.rossum.app/api/v1/annotations/320332/content/15984","category":"datapoint","schema_id":"sender_id",...},{"id":15985,"url":"https://<example>.rossum.app/api/v1/annotations/320332/content/15985","category":"datapoint","schema_id":"vat_detail_tax",...},...]}
In order to decrease the number of requests necessary for obtaining useful information about annotations, modifiers and documents can be sideloaded using query parametersideload. This parameter accepts comma-separated list of keywords:assignees,automation_blockers,confirmed_bys,content,creators,deleted_bys,documents,emails,exported_bys,labels,modifiers,notes,organizations,pages,purged_bys,queues,rejected_bys,related_emails,relations,child_relations,schemas,suggested_edits,workflow_runs,workspaces.
The response is then enriched by the requested keys, which contain lists of the sideloaded objects. Sideloadedcontentcan be filtered byschema_idto obtain only a subset of datapoints in content part of response, but is a deprecated feature and will be removed in the future.
Filter oncontentcan be specified using query parametercontent.schema_idthat accepts comma-separated list of requiredschema_ids.
sideload
assignees
automation_blockers
confirmed_bys
content
creators
deleted_bys
documents
emails
exported_bys
labels
modifiers
notes
organizations
pages
purged_bys
queues
rejected_bys
related_emails
relations
child_relations
schemas
suggested_edits
workflow_runs
workspaces
content
schema_id
content
content.schema_id
schema_id

#### Response

Status:200
200
Returnspaginatedresponse with a list ofannotationobjects.

### Create an annotation

Create an annotation

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"status": "created", "document": "https://<example>.rossum.app/api/v1/documents/315877", "queue": "https://<example>.rossum.app/api/v1/queues/8236", "content_data": [{category: "datapoint", schema_id: "doc_id", content: {value: "122"}, "validation_sources": []}], "values": {}, "metadata": {}}'\'https://<example>.rossum.app/api/v1/annotations'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"status": "created", "document": "https://<example>.rossum.app/api/v1/documents/315877", "queue": "https://<example>.rossum.app/api/v1/queues/8236", "content_data": [{category: "datapoint", schema_id: "doc_id", content: {value: "122"}, "validation_sources": []}], "values": {}, "metadata": {}}'\'https://<example>.rossum.app/api/v1/annotations'

```
{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/31336","pages":["https://<example>.rossum.app/api/v1/pages/561206"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"created","rir_poll_id":null,"messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null,...}
```

{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/31336","pages":["https://<example>.rossum.app/api/v1/pages/561206"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"created","rir_poll_id":null,"messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null,...}
POST /v1/annotations
POST /v1/annotations
Create an annotation object.
Normally you create annotations via theuploadendpoint.
This endpoint could be used for creating annotation instances including their content and withstatusset to an
explicitly requested value. Currently onlycreatedis supported which is not touched by the rest of the platform
and is not visible via the Rossum UI. This allows for subsequent updates before switching the status toimportingso that it is passed through the rest of the upload pipeline.
status
created
importing
The use-case for this is theupload.createdhook event where new
annotations could be created and the platform runtime then switches all such annotations' status toimporting.
upload.created
importing
KeytypeDescriptionRequiredstatusenumRequested annotation status. Onlycreatedis currently supported.YesdocumentURLAnnotation document.YesqueueURLTarget queue.Yescontent_datalist[object]Array of annotation data content objects.NovaluesobjectValues object as described inuploadendpoint.NometadataobjectClient data.Notraining_enabledboolFlag signalling whether the annotation should be used in the training of the instant learning component. Default istrue.No
created
true

#### Response

Status:200
200
Returnsannotationobject.

### Retrieve an annotation

Get annotation object315777
315777

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777'

```
{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/31336","pages":["https://<example>.rossum.app/api/v1/pages/561206"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","rir_poll_id":"54f6b9ecfa751789f71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null,...}
```

{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/31336","pages":["https://<example>.rossum.app/api/v1/pages/561206"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","rir_poll_id":"54f6b9ecfa751789f71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null,...}
GET /v1/annotations/{id}
GET /v1/annotations/{id}
Get an annotation object.

#### Response

Status:200
200
Returnsannotationobject.

### Update an annotation

Update annotation object315777
315777

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"document": "https://<example>.rossum.app/api/v1/documents/315877", "queue": "https://<example>.rossum.app/api/v1/queues/8236", "status": "postponed"}'\'https://<example>.rossum.app/api/v1/annotations/315777'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"document": "https://<example>.rossum.app/api/v1/documents/315877", "queue": "https://<example>.rossum.app/api/v1/queues/8236", "status": "postponed"}'\'https://<example>.rossum.app/api/v1/annotations/315777'

```
{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236",..."status":"postponed","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null}
```

{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236",..."status":"postponed","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null}
PUT /v1/annotations/{id}
PUT /v1/annotations/{id}
Update annotation object.

#### Response

Status:200
200
Returns updatedannotationobject.

### Update part of an annotation

Update status of annotation object315777
315777

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"status": "deleted"}'\'https://<example>.rossum.app/api/v1/annotations/315777'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"status": "deleted"}'\'https://<example>.rossum.app/api/v1/annotations/315777'

```
{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,..."status":"deleted","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null}
```

{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,..."status":"deleted","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null}
PATCH /v1/annotations/{id}
PATCH /v1/annotations/{id}
Update part of annotation object.

#### Response

Status:200
200
Returns updatedannotationobject.
confirmed
exported
confirmed
exported
purged
purged

### Copy annotation

Copy annotation315777to a queue8236
315777
8236

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"target_queue": "https://<example>.rossum.app/api/v1/queues/8236", "target_status": "to_review"}'\'https://<example>.rossum.app/api/v1/annotations/315777/copy'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"target_queue": "https://<example>.rossum.app/api/v1/queues/8236", "target_status": "to_review"}'\'https://<example>.rossum.app/api/v1/annotations/315777/copy'

```
{"annotation":"https://<example>.rossum.app/api/v1/annotations/320332"}
```

{"annotation":"https://<example>.rossum.app/api/v1/annotations/320332"}
POST /v1/annotations/{id}/copy
POST /v1/annotations/{id}/copy
Make a copy of annotation in another queue. All data and metadata are copied.
KeyDescriptiontarget_queueURL of queue, where the copy should be placed.target_statusStatus of copied annotation (if not set, it stays the same)
If you want to directly reimport the copied annotation, you can usereimport=truequery parameter (such annotation will be billed).
reimport=true

#### Response

Status:200
200
Returns URL of the new annotation object.

### Delete annotation

Delete annotation315777
315777

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777'
DELETE /v1/annotations/{id}
DELETE /v1/annotations/{id}
Delete an annotation object from the database.
It also deletes the related page objects.
Never call this internal API, mark theannotation as deletedinstead.

#### Response

Status:204
204

### Get suggested email recipients

Get315777and78590annotations suggested email recipients
315777
78590

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/315777", https://<example>.rossum.app/api/v1/annotations/78590]'\'https://<example>.rossum.app/api/v1/annotations/suggested_recipients'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/315777", https://<example>.rossum.app/api/v1/annotations/78590]'\'https://<example>.rossum.app/api/v1/annotations/suggested_recipients'

```
{"results":[{"source":"email_header","email":"don.joe@corp.us","name":"Don Joe"},...]}
```

{"results":[{"source":"email_header","email":"don.joe@corp.us","name":"Don Joe"},...]}
POST /v1/annotations/suggested_recipients
POST /v1/annotations/suggested_recipients
Retrieves annotations suggested email recipients depending on Queuessuggested recipients settings.

#### Response

Status:200
200
Returns a list ofsource objects.

#### Suggested recipients source object

ParameterDescriptionsourceSpecifies where the email is found, seepossible sourcesemailEmail address of the suggested recipientnameName of the suggested recipient. Either a value from an email header or a value from parsing the email address

### Purge deleted annotations

Purge deleted annotations from queue42
42

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/42"}'\'https://<example>.rossum.app/api/v1/annotations/purge_deleted'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/42"}'\'https://<example>.rossum.app/api/v1/annotations/purge_deleted'
POST /v1/annotations/purge_deleted
POST /v1/annotations/purge_deleted
Start the asynchronous process of purging customer's data related to selected annotations withdeletedstatus. The following operations will happen:
deleted
- deleteannotation data
- deletepages
- remove content and file names ofdocuments
- remove annotations fromrelationsoftypeduplicate
duplicate
- preserveannotationsobjects, move them topurgedstatus
purged
KeyTypeRequiredDescriptionannotationslist[URL]falseList of annotations to be purgedqueueURLfalseQueue of which the annotations should be purged.
At least one ofannotations,queuefields must be filled in. The resulting set of annotations is the disjunction ofqueueandannotationsfilter.
annotations
queue
queue
annotations

#### Response

Status:202
202
This is an asynchronous endpoint, status of annotations is changed topurgedand related objects are gradually being deleted.
purged

### Annotation time spent

Time spent information can be optionally passed along the following annotation endpoints:cancel,confirm,delete,edit,postpone,reject.
Confirm annotation315777and also update time spent data
315777

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"processing_duration": {"time_spent_active": 10.0, "time_spent_overall": 20.0, "time_spent_edit": 1.0, "time_spent_blockers": 2.0, "time_spent_emails": 3.0, "time_spent_opening": 1.5}}'\'https://<example>.rossum.app/api/v1/annotations/315777/confirm'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"processing_duration": {"time_spent_active": 10.0, "time_spent_overall": 20.0, "time_spent_edit": 1.0, "time_spent_blockers": 2.0, "time_spent_emails": 3.0, "time_spent_opening": 1.5}}'\'https://<example>.rossum.app/api/v1/annotations/315777/confirm'
POST /v1/annotations/{id}/cancel
POST /v1/annotations/{id}/cancel
POST /v1/annotations/{id}/confirm
POST /v1/annotations/{id}/confirm
POST /v1/annotations/{id}/delete
POST /v1/annotations/{id}/delete
POST /v1/annotations/{id}/edit
POST /v1/annotations/{id}/edit
POST /v1/annotations/{id}/postpone
POST /v1/annotations/{id}/postpone
POST /v1/annotations/{id}/reject
POST /v1/annotations/{id}/reject
Seeannotation processing durationobject.

### Get page spatial data

Get spatial data for two first pages of annotation1421
1421

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/1421/page_data?granularity=words&page_numbers=1,2'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/1421/page_data?granularity=words&page_numbers=1,2'

```
{"results":[{"page_number":1,"granularity":"words","items":[{"position":[120,22,33,44],"text":"full"},{"position":[180,22,33,44],"text":"of"},{"position":[180,22,33,44],"text":"eels"},]},{"page_number":2,"granularity":"words","items":[{"position":[120,22,33,44],"text":"it"},{"position":[180,22,33,44],"text":"is"},{"position":[180,22,33,44],"text":"scratched"},]},]}
```

{"results":[{"page_number":1,"granularity":"words","items":[{"position":[120,22,33,44],"text":"full"},{"position":[180,22,33,44],"text":"of"},{"position":[180,22,33,44],"text":"eels"},]},{"page_number":2,"granularity":"words","items":[{"position":[120,22,33,44],"text":"it"},{"position":[180,22,33,44],"text":"is"},{"position":[180,22,33,44],"text":"scratched"},]},]}
GET /v1/annotations/{id}/page_data
GET /v1/annotations/{id}/page_data
Get text content for every page, including position coordinates, considering granularity options like lines, words, characters, or complete page text content.
Query parameters:
KeyTypeDefaultDescriptionRequiredgranularitystrOne oflines,words,chars,texts,barcodes.Yespage_numbersstrFirst 20 pages of the documentComma separated page numbers. Max. 20 page numbers, if there is more, they are silently ignored.No
lines
words
chars
texts
barcodes

#### Response

Status:200
200
Response result objects consist of following keys:
KeyTypeDescriptionpage_numberintNumber of page.granularitystrOne oflines,words,chars,texts.itemslist[object]List of objects divided by the chosen granularity.
lines
words
chars
texts
Items consist of following keys:
KeyTypeDescriptionpositionlist[int]Coordinates of the item on the given page. In case oftextsgranularity, the result items objects are missingpositionkey, since thetextvalue is the full page text.textstrValue of the item.typestrType of barcode. This value is present only for granularitybarcodes.
texts
position
text
barcodes
Status:404
404
If there are no spatial data available for the given annotation.

### Translate page spatial data

Get the translation for spatial data for page 2 of the annotation1421
1421

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"target_language": "en", "granularity": "lines", "page_numbers": [2]}'\'https://<example>.rossum.app/api/v1/annotations/1421/page_data/translate'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"target_language": "en", "granularity": "lines", "page_numbers": [2]}'\'https://<example>.rossum.app/api/v1/annotations/1421/page_data/translate'

```
{"results":[{"page_number":2,"granularity":"lines","items":[{"position":[120,22,33,44],"text":"My hovercraft is"},{"position":[180,22,33,44],"text":"full of eels"},]},]}
```

{"results":[{"page_number":2,"granularity":"lines","items":[{"position":[120,22,33,44],"text":"My hovercraft is"},{"position":[180,22,33,44],"text":"full of eels"},]},]}
POST /v1/annotations/{id}/page_data/translate
POST /v1/annotations/{id}/page_data/translate
Get translation for all lines on a page, including position coordinates. Source language of the page is automatically detected. Translated text
of a page in a particular language is cached for 60 days.
AttributeTypeDefaultDescriptionRequiredgranularitystrCurrently supported options:lines.Yespage_numberslist[int]Number of the page to be translated. Only one page at a time is currently supported.Yestarget_languagestrLanguage* to translate the spatial data to.Yes
lines
*target_languagefield must be either in ISO 639-1 two-digit language code format or a combination of
ISO 639-1 two-digit language code followed by an underscore followed by an ISO 3166 2-digit country code. Supported languages
and their codes are as follows:
target_language
KeyDescriptionafAfrikaanssqAlbanianamAmharicarArabichyArmenianazAzerbaijanibnBengalibsBosnianbgBulgariancaCatalanzhChinese (Simplified)zh-TWChinese (Traditional)hrCroatiancsCzechdaDanishfa-AFDarinlDutchenEnglishetEstonianfaFarsi (Persian)tlFilipino, TagalogfiFinnishfrFrenchfr-CAFrench (Canada)kaGeorgiandeGermanelGreekguGujaratihtHaitian CreolehaHausaheHebrewhiHindihuHungarianisIcelandicidIndonesiangaIrishitItalianjaJapaneseknKannadakkKazakhkoKoreanlvLatvianltLithuanianmkMacedonianmsMalaymlMalayalammtMaltesemrMarathimnMongoliannoNorwegian (Bokmål)psPashtoplPolishptPortuguese (Brazil)pt-PTPortuguese (Portugal)paPunjabiroRomanianruRussiansrSerbiansiSinhalaskSlovakslSloveniansoSomaliesSpanishes-MXSpanish (Mexico)swSwahilisvSwedishtaTamilteTeluguthThaitrTurkishukUkrainianurUrduuzUzbekviVietnamesecyWelsh

#### Response

Status:200
200
Response result objects consist of following keys:
KeyTypeDescriptionpage_numberintNumber of page.granularitystrCurrently supported options:lines.itemslist[object]List of translated objects divided by the chosen granularity.
lines
Items consist of following keys:
KeyTypeDescriptionpositionlist[int]Coordinates of the item on the given page.textstrTranslated text.
Status:404
404
If there are no spatial data available for the requested pages/annotation.


## Annotation Data

Example annotation data

```
{"content":[{"id":27801931,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801931","children":[{"id":27801932,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801932","content":{"value":"2183760194","normalized_value":"2183760194","page":1,"position":[761,48,925,84],"rir_text":"2183760194","rir_position":[761,48,925,84],"connector_text":null,"rir_confidence":0.99234},"category":"datapoint","schema_id":"document_id","validation_sources":["score"],"time_spent":0,"time_spent_overall":0,"hidden":false},{"id":27801933,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801933","content":{"value":"6/8/2018","normalized_value":"2018-08-06","page":1,"position":[283,300,375,324],"rir_text":"6/8/2018","rir_position":[283,300,375,324],"connector_text":null,"rir_confidence":0.98279},"category":"datapoint","schema_id":"date_issue","validation_sources":["score"],"time_spent":0,"time_spent_overall":0,"hidden":false},{"id":27801934,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801934","content":null,"category":"datapoint","schema_id":"email_button","validation_sources":["NA"],"time_spent":0,"time_spent_overall":0,"hidden":false},...}]}
```

{"content":[{"id":27801931,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801931","children":[{"id":27801932,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801932","content":{"value":"2183760194","normalized_value":"2183760194","page":1,"position":[761,48,925,84],"rir_text":"2183760194","rir_position":[761,48,925,84],"connector_text":null,"rir_confidence":0.99234},"category":"datapoint","schema_id":"document_id","validation_sources":["score"],"time_spent":0,"time_spent_overall":0,"hidden":false},{"id":27801933,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801933","content":{"value":"6/8/2018","normalized_value":"2018-08-06","page":1,"position":[283,300,375,324],"rir_text":"6/8/2018","rir_position":[283,300,375,324],"connector_text":null,"rir_confidence":0.98279},"category":"datapoint","schema_id":"date_issue","validation_sources":["score"],"time_spent":0,"time_spent_overall":0,"hidden":false},{"id":27801934,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801934","content":null,"category":"datapoint","schema_id":"email_button","validation_sources":["NA"],"time_spent":0,"time_spent_overall":0,"hidden":false},...}]}
Annotation data is used by the Rossum UI to display annotation data properly. Be
aware that values in attributevaluearenotnormalized (e.g. numbers, dates) and data structure
may be changed to accommodate UI requirements.
value
Top levelcontentcontains a list of section objects.resultsis currently
a copy ofcontentand is deprecated.
content
results
content
Section objects:
AttributeTypeDescriptionRead-onlyidint64A unique ID of a given section.trueurlURLURL of the section.trueschema_idstringReference mapping the object to the schema tree.categorystringsectionchildrenlistArray specifying objects that belong to the section.
section
Datapoint, multivalue and tuple objects:
AttributeTypeDescriptionRead-onlyidint64A unique ID of a given object.trueurlURLURL of a given object.trueschema_idstringReference mapping the object to the schema tree.categorystringType of the object (datapoint,multivalueortuple).truechildrenlistArray specifying child objects. Only available formultivalueandtuplecategories.truecontentobject(optional) A dictionary of the attributes of a given datapoint (only available fordatapoint) seebelowfor details.truevalidation_sourceslist[object]Source of validation of the extracted data, see below.time_spentfloat(optional) Time spent while actively working on a given node, in seconds.time_spent_overallfloat(optional) Total time spent while validating a given node, in seconds. (only for internal purposes).time_spent_gridfloat(optional) Total time spent while actively working on a grid, in seconds. Only available formultivaluecategory. (only for internal purposes).time_spent_grid_overallfloat(optional) Total time spent while validating a given grid, in seconds. Only available formultivaluecategory. (only for internal purposes).hiddenboolIf set to true, the datapoint is not visible in the user interface, but remains stored in the database.no_recalculationboolIf set to true, the datapoint's formula is not recalculated automatically. Only available fordatapointcategory editable formula datapoints. seebelowgridobjectSpecify grid structure, seebelowfor details. Only allowed for multivalue object.
datapoint
multivalue
tuple
multivalue
tuple
datapoint
multivalue
multivalue
datapoint

#### Time spent

Time spents on datapoint are in seconds and are stored on datapoint object, for categorymultivalueordatapoint. For time spent on the annotation level, seeannotation processing duration.
multivalue
datapoint
Active time spent is stored intime_spent.
Overall time spent is stored intime_spent_overall.
Active time spent with an active magic grid is stored intime_spent_grid.
Overall time spent with an active magic grid is stored intime_spent_grid_overall.
time_spent
time_spent_overall
time_spent_grid
time_spent_grid_overall
Measuring starts when an annotation is not in a read-only mode after selecting a datapoint.
Measuring ends when:
- another datapoint is selected. Selecting of datapoints when showing automation blockers doesn’t end or affect the measuring.
- the user leaves an annotation (for the same reasons as measuring ends on an annotation)
- the user goes to edit mode
When a measuring ends time_spent of the previously selected datapoint is incremented by measured time_spent and the result is patched together with adding a human validation source to validation sources.

#### Content object

Can be null for datapoints of typebutton
button
AttributeTypeDescriptionRead-onlyvaluestringThe extracted data of a given node. Maximum length: 1500 UTF characters.normalized_valuestringNormalized value for date (in ISO 8601 format) and number fields (in JSON number format).pageintNumber of page where the data is situated (see position).positionlistList of the coordinates of the label box of the given node. (left, top, right, bottom)rir_textstringThe extracted text, used as a reference for data extraction models.truerir_raw_textstringRaw extracted text (only for internal purposes, may be removed in the future).truerir_pageintThe extracted page, used as a reference for data extraction models.truerir_positionlistThe extracted position, used as a reference for data extraction models. (left, top, right, bottom)truerir_confidencefloatConfidence (estimated probability) that this field was extracted correctly.trueconnector_textstringText set by the connector.trueconnector_positionlistPosition set by the connector. (left, top, right, bottom)trueocr_textstringValue extracted by OCR, if applicable. (only for internal purposes, may be removed in the future)trueocr_raw_textstringRaw value extracted by OCR, if applicable. (only for internal purposes, may be removed in the future)trueocr_positionstringOCR position, if applicable. (left, top, right, bottom) (only for internal purposes, may be removed in the future)true
When bothvalueandnormalized_valueis set,normalized_valueis ignored on update.
value
normalized_value
normalized_value

#### Formula datapoints

Fordatapointcategory fields which have their schemaUI configuration'stypeproperty set toformulathe datapoint content and attributes are being updated automatically based on the provided formula code.
datapoint
type
formula
For editable formula fields (i.e. the correspondingUI configuration'seditproperty is not set
todisabledoption) the automatic recalculation can be disabled by setting the datapointno_recalculationflag to true.
To re-enable the formula automatic recalculation set theno_recalculationflag to false.
edit
disabled
no_recalculation
no_recalculation

#### Validation sources

validation_sourcesproperty is a list of sources that verified the extracted data. When the list is
non-empty, datapoint is considered to be validated (and no eye-icon is displayed next to it in the Rossum UI).
validation_sources
Currently, these are the sources of validation:
- score:confidence score coming from the AI Core Enginewas higher than a preset score threshold (can be set onqueue, or individually perdatapointin schema; default is 0.8).
- checks:Data extractor does several checks like summing up tax_details, which can verify that the data were extracted correctly.
- not_found:Value was not found by the AI engine. As we do not report confidence in such cases yet, we add a validation source instead. It will be removed as soon as we have confidence present for field that were not found.
- data_matchingSet by a hook when, for example, the datapoint matches some other database.
- history:Several fields can be confirmed from historical data in exported documents (can be turned on/off on per queue basis using autopilot section in its settings).
- connector:A connector verified the validity.
- table_suggester:Used internally for the complex line items user interface.
- rules:Added from rules and actions on a queue.
- human:An operator visited the field in validation interface (assumed just verifying the value, not necessarily making any corrections).
- non_required:Value was not found, is non-required and has no rir_field_name set.
Additional possible validation source valueNAsigns that validation sources are "Not Applicable" and may now occur only for button datapoints.
The list is subject to ongoing expansion.
Example multivalue datapoint object with a grid

```
{"id":122852,"schema_id":"line_items","category":"multivalue","time_spent":3.4,"time_spent_overall":4.5,"time_spent_grid":1.2,"time_spent_grid_overall":2.3,"grid":{"parts":[{"page":1,"columns":[{"left_position":348,"schema_id":"item_description","header_texts":["Description"]},{"left_position":429,"schema_id":"item_quantity","header_texts":["Qty"]}],"rows":[{"top_position":618,"tuple_id":null,"type":"header"},{"top_position":649,"tuple_id":123,"type":"data"}],"width":876,"height":444}]},...}
```

{"id":122852,"schema_id":"line_items","category":"multivalue","time_spent":3.4,"time_spent_overall":4.5,"time_spent_grid":1.2,"time_spent_grid_overall":2.3,"grid":{"parts":[{"page":1,"columns":[{"left_position":348,"schema_id":"item_description","header_texts":["Description"]},{"left_position":429,"schema_id":"item_quantity","header_texts":["Qty"]}],"rows":[{"top_position":618,"tuple_id":null,"type":"header"},{"top_position":649,"tuple_id":123,"type":"data"}],"width":876,"height":444}]},...}
Grid object (for internal use only) is used to store table vertical and horizontal separators and
related attributes. Every grid consists of zero or moreparts.
parts
Everypartobject consists of several attributes:
part
AttributeTypeDescriptionpageintA unique ID of a given object.columnslist[object]Description of grid columns.rowslist[object]Description of grid rows.widthfloatTotal width of the grid.heightfloatTotal height of the grid.
Every column contains attributes:
AttributeTypeDescriptionleft_positionfloatPosition of the column left edge.schema_idstringReference to datapoint schema id. Used ingrid-to-table conversion.header_textslist[string]Extracted texts from column headers.
Every row contains attributes:
AttributeTypeDescriptiontop_positionfloatPosition of the row top edge.tuple_idintId of the corresponding tuple datapoint if it exists else null.typestringRow type. Allowed values are specified in the schema, seegrid. Ifnull, the row is ignored duringgrid-to-table conversion.
null
Currently, it is only allowed to have one part per page (for a particular grid).
"type": null

### Get the annotation data

Get annotation data of annotation315777
315777

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/content'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/content'
GET /v1/annotations/{id}/content
GET /v1/annotations/{id}/content
Get annotation data.

#### Response

Status:200
200
Returns annotation data.

### Update annotation data

Update annotation data of annotation315777
315777

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": [{"category": "section", "schema_id": "invoice_details_section", "children": [{"category": "datapoint", "schema_id": "document_id", "content": {"value": "12345"}, "validation_sources": ["human"], "type": "string", "rir_confidence": 0.99}]}]}'\'https://<example>.rossum.app/api/v1/annotations/315777/content'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": [{"category": "section", "schema_id": "invoice_details_section", "children": [{"category": "datapoint", "schema_id": "document_id", "content": {"value": "12345"}, "validation_sources": ["human"], "type": "string", "rir_confidence": 0.99}]}]}'\'https://<example>.rossum.app/api/v1/annotations/315777/content'

```
{"content":[{"category":"section","schema_id":"invoice_details_section","children":[{"category":"datapoint","schema_id":"document_id","content":{"value":"12345"},"type":"string","validation_sources":["human"]}]}]}
```

{"content":[{"category":"section","schema_id":"invoice_details_section","children":[{"category":"datapoint","schema_id":"document_id","content":{"value":"12345"},"type":"string","validation_sources":["human"]}]}]}
PATCH /v1/annotations/{id}/content
PATCH /v1/annotations/{id}/content
Update annotation data. The format is the same as for GET, datapoints missing in the uploaded content are preserved.

#### Response

Status:200
200
Returns annotation data.

### Bulk update annotation data

Example of body for bulk update of annotation data

```
{"operations":[{"op":"replace","id":"198143","value":{"content":{"value":"John","position":[103,110,121,122],"page":1},"hidden":false,"options":[],"validation_sources":["human"]}},{"op":"remove","id":"884061"},{"op":"add","id":"884060","value":[{"schema_id":"item_description","content":{"page":1,"position":[162,852,371,875],"value":"Bottle"}}]}]}
```

{"operations":[{"op":"replace","id":"198143","value":{"content":{"value":"John","position":[103,110,121,122],"page":1},"hidden":false,"options":[],"validation_sources":["human"]}},{"op":"remove","id":"884061"},{"op":"add","id":"884060","value":[{"schema_id":"item_description","content":{"page":1,"position":[162,852,371,875],"value":"Bottle"}}]}]}
POST /v1/annotations/{id}/content/operations
POST /v1/annotations/{id}/content/operations
Allows to specify a sequence of operations that should be performed
on particular datapoint objects.
To replace adatapointvalue (or other supported attribute), usereplaceoperation:
datapoint
KeyTypeDescriptionopstringType of operation:replaceidintegerDatapoint idvalueobjectUpdated data, format is the same as inAnotation Data. Onlyvalue(*),position,page,validation_sources,hiddenandoptionsattributes may be updated. Please note thatvalueis parsed and formatted.
replace
value
position
page
validation_sources
hidden
options
value
(*)normalized_valuemay also be specified. When bothvalueandnormalized_valueare specified, they must match, otherwise datapoint won't be modified (this may be changed in the future).
normalized_value
value
normalized_value
Please note thatsection,multivalueandtupleshould not be updated.
section
multivalue
tuple
To add a new row into a tablemultivalue, useaddoperation:
multivalue
KeyTypeDescriptionopstringType of operation:addidintegerMultivalue id (parent of new datapoint)valuelist[object]Added row data. List of objects, format of the object is the same as inAnotation Data.schema_idattribute is required, onlyvalue,position,page,validation_sources,hiddenandoptionsattributes may be set.validation_sourceslist[object](optional) List of validation sources to set for all fields of the row by default (unless overriden invalue). This allows easily adding rows without breaking automation. See the "Validation sources" section below.
add
schema_id
value
position
page
validation_sources
hidden
options
value
The row will be appended to the current list of rows.
For simple multivalues, the add operation can be used to add one child datapoint:
KeyTypeDescriptionopstringType of operation:addidintegerMultivalue id (parent of new datapoint)valueobjectUpdated data, format is the same as inAnotation Data. Onlyvalue(*),position,page,validation_sources,hiddenandoptionsattributes may be updated. Please note thatvalueis parsed and formatted.
add
value
position
page
validation_sources
hidden
options
value
To remove a row from a multivalue, useremoveoperation:
KeyTypeDescriptionopstringType of operation:removeidintegerDatapoint id
remove
Please note that onlymultivaluechildren datapoints may be removed.
multivalue

#### Response

Status:200
200
Returns annotation data.

### Replace annotation data by OCR

Replace annotation data value by text extracted from a rectangle

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"rectangle": [316.2, 533.9, 352.7, 556.5], "page": "https://<example>.rossum.app/api/v1/pages/12221"}'\'https://<example>.rossum.app/api/v1/annotations/319668/content/21233223/select"
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"rectangle": [316.2, 533.9, 352.7, 556.5], "page": "https://<example>.rossum.app/api/v1/pages/12221"}'\'https://<example>.rossum.app/api/v1/annotations/319668/content/21233223/select"
POST /v1/annotations/{id}/content/{id of child node}/select
POST /v1/annotations/{id}/content/{id of child node}/select
Replace annotation data by OCR extracted from the rectangle of the document page. Payload of the request:
KeyTypeDescriptionrectanglelist[float]Bounding box of an occurrence.pageURLPage of occurrence.
When the rectangle size is unsuitable for OCR (any rectangle side is smaller
than 4 px), rectangle is extended to cover the text that overlaps with the
rectangle.

#### Response

Status:200
200
Returns annotation data.

### Grid operations

Update multiple grid parts and perform OCR on created and updated grids

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"operations": [{"op": "update", "grid_index": 0, "grid": {"page": 1, "columns": [...], "rows": [...]}}]}'\'https://elis.rossum.ai/api/v1/annotations/319668/content/21233223/grid_operations"
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"operations": [{"op": "update", "grid_index": 0, "grid": {"page": 1, "columns": [...], "rows": [...]}}]}'\'https://elis.rossum.ai/api/v1/annotations/319668/content/21233223/grid_operations"
POST /v1/annotations/{id}/content/{id of the multivalue}/grid_operations
POST /v1/annotations/{id}/content/{id of the multivalue}/grid_operations
This endpoint applies multiple operations on multiple grids for one multivalue and perform OCR if required, and update the multivalue with the resulting grid.
Forupdateoperation the position of the grid and its rows and columns can be changed, the column layout can be changed, but the row structure must be unchanged.
update
Payload of the request:
KeyTypeDescriptionoperationslist[object]List of operations to apply to the grid
Single operations:
KeyTypeDescriptionRequiredopstrupdateordeleteorcreateYesgrid_indexintIndex of the grid,YesgridobjectNew grid partForcreateandupdateoperations
update
delete
create
create
update
The operations are applied sequentially. Thegrid_indexcorresponds to the index of the grid parts when the operation is applied. Combining different types of operations is not supported.
grid_index

#### Response

Status:200
200
Returns updated multivalue content as a tree, with only updated datapoints.

### Partial grid updates

Update a grid part and perform OCR on modified cell datapoints

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"grid_index": 0, "grid": {"page": 1, "columns": [...], "rows": [...]}, "operations": {"columns": [{"op": "update", "schema_id": "vat_rate"}], "rows": [{"op": "delete", "tuple_id": 1256}]}'\'https://elis.rossum.ai/api/v1/annotations/319668/content/21233223/grid_parts_operations"
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"grid_index": 0, "grid": {"page": 1, "columns": [...], "rows": [...]}, "operations": {"columns": [{"op": "update", "schema_id": "vat_rate"}], "rows": [{"op": "delete", "tuple_id": 1256}]}'\'https://elis.rossum.ai/api/v1/annotations/319668/content/21233223/grid_parts_operations"
POST /v1/annotations/{id}/content/{id of the multivalue}/grid_parts_operations
POST /v1/annotations/{id}/content/{id of the multivalue}/grid_parts_operations
Apply multiple operations on a grid and perform OCR on modified cell datapoints. Update the multivalue with the new grid.
Query parameters
Query parameterTypeDefaultRequiredDescriptionfull_responsebooleanfalsefalseUse this parameter to get all datapoints in the grid part in the response
Payload of the request:
KeyTypeDescriptionoperationsobjectOperations to apply to the gridgridobjectUpdated grid partgrid_indexintIndex of the grid part
Operations are grouped inrowsoperations andcolumnsoperations:
rows
columns
KeyTypeDescriptionrowslist[object]List of row operationscolumnslist[object]List of column operations
Single operations must contain the following parameters:
KeyTypeDescriptionopstrupdateordeleteorcreaterow_indexintRequired for rowupdateand rowcreateoperationstuple_idintId of the tuple datapoint, required for rowdeleteand rowupdateoperationsschema_idintId of the schema, required for column operations
update
delete
create
update
create
delete
update
Possible operations:
axisoprequired parametersOCRResultcolumnsupdateschema_idYesUpdate column datapointscolumnsdeleteschema_idNoSet content to empty for column datapointsrowscreaterow_indexYesInsert a new row, create datapoints and perform OCRrowsupdaterow_index, tuple_idYesUpdate datapoints via OCRrowsdeletetuple_idNoDelete the tuple associated to this row
OCR is performed only for rows of extractable type as defined in the multivalue schema byrow_types_to_extract, or by default for rows of typedataonly.
row_types_to_extract
data

#### Response

Status:200
200
Returns updated multivalue content as a tree. By default, only updated datapoints and updated grid are returned. Add?full_response=trueto the url to get in the response all the datapoints in this grid.
?full_response=true

### Send updated annotation data

Send feedback on annotation315777
315777
Start the annotation

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/start'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/start'

```
{"annotation":"https://<example>.rossum.app/api/v1/annotations/315777","session_timeout":"01:00:00"}
```

{"annotation":"https://<example>.rossum.app/api/v1/annotations/315777","session_timeout":"01:00:00"}
Get the annotation data

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/content'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/content'

```
{"id":37507206,"url":"https://<example>.rossum.app/api/v1/annotations/315777/content/37507206","content":{"value":"001","page":1,"position":[302,91,554,56],"rir_text":"000957537","rir_position":[302,91,554,56],"connector_text":null,"rir_confidence":null},"category":"datapoint","schema_id":"document_id","validation_sources":["human"],"time_spent":2.7,"time_spent_overall":6.1,"hidden":false}
```

{"id":37507206,"url":"https://<example>.rossum.app/api/v1/annotations/315777/content/37507206","content":{"value":"001","page":1,"position":[302,91,554,56],"rir_text":"000957537","rir_position":[302,91,554,56],"connector_text":null,"rir_confidence":null},"category":"datapoint","schema_id":"document_id","validation_sources":["human"],"time_spent":2.7,"time_spent_overall":6.1,"hidden":false}
Patch the annotation

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"content": {"value": "#INV00011", "position": [302, 91, 554, 56]}}'\'https://<example>.rossum.app/api/v1/annotations/315777/content/37507206'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"content": {"value": "#INV00011", "position": [302, 91, 554, 56]}}'\'https://<example>.rossum.app/api/v1/annotations/315777/content/37507206'

```
{"id":37507206,"url":"https://<example>.rossum.app/api/v1/annotations/431694/content/39125535","content":{"value":"#INV00011","page":1,"position":[302,91,554,56],"rir_text":"","rir_position":null,"rir_confidence":null,"connector_text":null},"category":"datapoint","schema_id":"document_id","validation_sources":[],"time_spent":0,"time_spent_overall":0,"hidden":false}
```

{"id":37507206,"url":"https://<example>.rossum.app/api/v1/annotations/431694/content/39125535","content":{"value":"#INV00011","page":1,"position":[302,91,554,56],"rir_text":"","rir_position":null,"rir_confidence":null,"connector_text":null},"category":"datapoint","schema_id":"document_id","validation_sources":[],"time_spent":0,"time_spent_overall":0,"hidden":false}
Confirm the annotation

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/confirm'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/confirm'
PATCH /v1/annotations/{id}/content/{id of the child node}
PATCH /v1/annotations/{id}/content/{id of the child node}
Update a particular annotation content node.
It is enough to pass just the updated attributes in the PATCH payload.
schema_id

#### Response

Status:200
200
Returns updated annotation data for the given node.


## Annotation Processing Duration

Example annotation processing duration

```
{"annotation":"https://<example>.rossum.app/api/v1/annotations/1","time_spent_active":12.3,"time_spent_overall":23.4,"time_spent_edit":1.23,"time_spent_blockers":2.34,"time_spent_emails":3.45,"time_spent_opening":4.56}
```

{"annotation":"https://<example>.rossum.app/api/v1/annotations/1","time_spent_active":12.3,"time_spent_overall":23.4,"time_spent_edit":1.23,"time_spent_blockers":2.34,"time_spent_emails":3.45,"time_spent_opening":4.56}
Annotation processing duration stores additional time spent information for an Annotation.
Annotation processing duration object:
AttributeTypeDescriptionRead-onlyOptionalannotationURLAnnotation that the processing duration is related totruetime_spent_activefloatTotal active time spent on the annotation, in secondstruetime_spent_overallfloatTotal time spent on the annotation, in seconds (same value as Annotation.time_spent)truetime_spent_editfloatTime spent editing the annotation, in secondstruetime_spent_blockersfloatTime spent on annotation blockers, in secondstruetime_spent_emailsfloatTime spent on emails, in secondstruetime_spent_openingfloatTime spent opening the annotation, in secondstrue
Measuring of time spent starts after an annotation is successfully started and datapoints and schema for annotation are fetched.
Measuring ends when:
- user changes annotation status (confirm, postpone, delete, reject)
- user leaves validation (goes back to dashboard or another page)
- user goes to the next annotation
- user confirms changes in edit mode
- annotation time expires (checked periodically every 5 minutes if the current annotation is inreviewingstate)
reviewing
- user closes a tab
time_spent_overallis the total time spent on the annotation,time_spent_activeis the same but measurement is stopped after 10 seconds of inactivity (no mouse movement nor key stroke or inactive tab).
time_spent_overall
time_spent_active

### Get the annotation processing duration

Get annotation processing duration of annotation315777
315777

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/processing_duration'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/processing_duration'
GET /v1/annotations/{id}/processing_duration
GET /v1/annotations/{id}/processing_duration
Get annotation processing duration.

#### Response

Status:200
200
Returns annotation processing duration.

### Update annotation processing duration

Update annotation processing duration of annotation315777
315777

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"time_spent_active": 10.00, "time_spent_overall": 20.0, "time_spent_edit": 1.0, "time_spent_blockers": 2.0, "time_spent_emails": 3.0, "time_spent_opening": 1.5}'\'https://<example>.rossum.app/api/v1/annotations/315777/processing_duration'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"time_spent_active": 10.00, "time_spent_overall": 20.0, "time_spent_edit": 1.0, "time_spent_blockers": 2.0, "time_spent_emails": 3.0, "time_spent_opening": 1.5}'\'https://<example>.rossum.app/api/v1/annotations/315777/processing_duration'

```
{"annotation":"https://<example>.rossum.app/api/v1/annotations/315777","time_spent_active":10.0,"time_spent_overall":20.0,"time_spent_edit":1.0,"time_spent_blockers":2.0,"time_spent_emails":2.0,"time_spent_opening":1.5}
```

{"annotation":"https://<example>.rossum.app/api/v1/annotations/315777","time_spent_active":10.0,"time_spent_overall":20.0,"time_spent_edit":1.0,"time_spent_blockers":2.0,"time_spent_emails":2.0,"time_spent_opening":1.5}
PATCH /v1/annotations/{id}/processing_duration
PATCH /v1/annotations/{id}/processing_duration
Update annotation processing duration.

#### Response

Status:200
200
Returns annotation processing duration.


## Audit log

Audit log represents a log record of actions performed by users.
Only admin or organization group admins can access the log records.
Logs do not include records about changes made by Rossum representatives via internal systems. The log retention policy is set to 1 year.
AttributeTypeDescriptionorganization_idintegerID of the organization.timestamp*strTimestamp of the log record.usernamestrUsername of the user that performed the action.object_idintID of the object on which the action was performed.object_typestrType of the object on which the action was performed.actionstrType of the action performed.contentobjectDetailed content of the action.
*Timestamp is of the ISO 8601 format with UTC timezone e.g.2024-07-01T07:00:00.000000
2024-07-01T07:00:00.000000
contentconsists of the following elements:
content
AttributeTypeDescriptionpathstrPartial URL path of the request.methodstrMethod of the request.request_idstrID of the request. Use this when contacting Rossum support with any related questions.status_codeintStatus code of the response.detailsobjectDetails about the request (if available). For most cases, this field will be{}.
{}
detailsmay include following attributes:
details
AttributeTypeDescriptiongroupslistName of theuser rolesthat were sent (if sent) in a request on a user object.

### List all audit logs

List all audit logs for update actions on user objects

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/audit_logs?object_type=user&action=update'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/audit_logs?object_type=user&action=update'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"object_type":"user","action":"update","username":"john.doe@example.com","object_id":131,"timestamp":"2024-07-01T07:00:00.000000","details":{"path":"api/v1/users/131","method":"PATCH","request_id":"0aadfd75-8dcz-4e62-94d9-a23811d0d0b0","status_code":200,"payload":{"groups":["admin"]},}}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"object_type":"user","action":"update","username":"john.doe@example.com","object_id":131,"timestamp":"2024-07-01T07:00:00.000000","details":{"path":"api/v1/users/131","method":"PATCH","request_id":"0aadfd75-8dcz-4e62-94d9-a23811d0d0b0","status_code":200,"payload":{"groups":["admin"]},}}]}
GET /v1/audit_logs
GET /v1/audit_logs
List audit log records for chosen objects and actions.
Using filters, you can narrow down the number of records.object_typeis a required filter.
object_type
Supported filters:
AttributeTypeDescriptionRequiredobject_typestrType of the object on which the action was performed. Available types aredocument,annotation,user.YesactionstrType of the action performed. See below.Noobject_idintID of the object on which the action was performed.Notimestamp_beforestrFilter for log entries before the given timestamp.Notimestamp_afterstrFilter for log entries after the given timestamp.NousernamestrUsername of the user that performed the action.No
document
annotation
user
Depending on theobject_type, you can choose to filter the logs based onaction. Eachobject_typesupports filtering by different actions:
object_type
action
object_type
object_typeAvailable actionsdocumentcreateannotationupdate-statususercreate, delete, purge, update, destroy, app_load*, reset-password, change_password
*app_loadvalue represents records of whenapi/v1/auth/userendpoint was called
app_load
api/v1/auth/user

#### Response

Status:200
200
Returnspaginatedresponse with a list ofaudit logsobjects.


## Automation blocker

Example automation blocker object

```
{"id":1,"url":"https://<example>.rossum.app/api/v1/automation_blockers/1","annotation":"https://<example>.rossum.app/api/v1/annotations/4","content":[{"level":"datapoint","type":"low_score","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"score":0.901,"threshold":0.975}}]},{"level":"datapoint","type":"failed_checks","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234,"details":{"validation":"bad"}}},{"level":"datapoint","type":"no_validation_sources","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234}},{"level":"datapoint","type":"error_message","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"message_content":["Error 1","Error 2"]}}]},{"level":"annotation","type":"suggested_edit_present"},{"level":"annotation","type":"is_duplicate"},{"level":"annotation","type":"error_message","details":{"message_content":["Error 1"]}}]}
```

{"id":1,"url":"https://<example>.rossum.app/api/v1/automation_blockers/1","annotation":"https://<example>.rossum.app/api/v1/annotations/4","content":[{"level":"datapoint","type":"low_score","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"score":0.901,"threshold":0.975}}]},{"level":"datapoint","type":"failed_checks","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234,"details":{"validation":"bad"}}},{"level":"datapoint","type":"no_validation_sources","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234}},{"level":"datapoint","type":"error_message","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"message_content":["Error 1","Error 2"]}}]},{"level":"annotation","type":"suggested_edit_present"},{"level":"annotation","type":"is_duplicate"},{"level":"annotation","type":"error_message","details":{"message_content":["Error 1"]}}]}
Automation blocker stores reason whyannotationwas notautomated.
AttributeTypeRead-onlyDescriptionidintegeryesAutomationBlocker object ID.urlURLyesAutomationBlocker object URL.annotationURLyesURL of related Annotation object.contentlist[object]noList of reasons why automation is blocked.
Content consists of following elements
AttributeTypeDescriptionlevelenumDesignates whether automation blocker relates to specificdatapointor to the wholeannotation.typeenumSee below forpossible values.schema_idstringOnly fordatapointlevel objects.sampleslist[object]Contains sample of specific datapoints with detailed info (only fordatapointlevel objects). Only first 10 samples are listed.samples_truncatedboolWhether number samples were truncated to 10, or contains all of them.detailsobjectOnly forlevel:annotationwithtype:error_message. Containsmessage_contentwith list of error messages.
datapoint
annotation
datapoint
datapoint
level
annotation
type
error_message
message_content

#### Automation blocker types

low_scoreautomation blocker example
low_score

```
{"level":"datapoint","type":"low_score","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"score":0.901,"threshold":0.975}},{"datapoint_id":1235,"details":{"score":0.968,"threshold":0.975}}]}
```

{"level":"datapoint","type":"low_score","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"score":0.901,"threshold":0.975}},{"datapoint_id":1235,"details":{"score":0.968,"threshold":0.975}}]}
failed_checksautomation blocker example
failed_checks

```
{"level":"datapoint","type":"failed_checks","schema_id":"schema_id","samples_truncated":false,"samples":[{"datapoint_id":43,"details":{"validation":"bad"}}]}
```

{"level":"datapoint","type":"failed_checks","schema_id":"schema_id","samples_truncated":false,"samples":[{"datapoint_id":43,"details":{"validation":"bad"}}]}
no_validation_sourcesautomation blocker example
no_validation_sources

```
{"level":"datapoint","type":"no_validation_sources","schema_id":"schema_id","samples_truncated":false,"samples":[{"datapoint_id":412}]}
```

{"level":"datapoint","type":"no_validation_sources","schema_id":"schema_id","samples_truncated":false,"samples":[{"datapoint_id":412}]}
error_messageautomation blocker example
error_message

```
[{"level":"annotation","type":"error_message","details":{"message_content":["annotation error"]}},{"level":"datapoint","type":"error_message","schema_id":"schema_id","samples_truncated":false,"samples":[{"datapoint_id":45,"details":{"message_content":["longer than 3 characters"]}}]}]
```

[{"level":"annotation","type":"error_message","details":{"message_content":["annotation error"]}},{"level":"datapoint","type":"error_message","schema_id":"schema_id","samples_truncated":false,"samples":[{"datapoint_id":45,"details":{"message_content":["longer than 3 characters"]}}]}]
delete_recommendationsautomation blocker example
delete_recommendations

```
[{"level":"annotation","type":"delete_recommendation_filename | delete_recommendation_page_count","details":{"message_content":["annotation error"]}},{"level":"datapoint","type":"delete_recommendation_field","schema_id":"document_type","samples_truncated":false,"samples":[{"datapoint_id":45}]}]
```

[{"level":"annotation","type":"delete_recommendation_filename | delete_recommendation_page_count","details":{"message_content":["annotation error"]}},{"level":"datapoint","type":"delete_recommendation_field","schema_id":"document_type","samples_truncated":false,"samples":[{"datapoint_id":45}]}]
extensionautomation blocker example
extension

```
[{"level":"annotation","type":"extension","details":{"content":["PO not found in the master data!"]}},{"level":"datapoint","type":"extension","schema_id":"sender_name","samples_truncated":false,"samples":[{"datapoint_id":1357,"details":{"content":["Unregistered vendor"]}}]}]
```

[{"level":"annotation","type":"extension","details":{"content":["PO not found in the master data!"]}},{"level":"datapoint","type":"extension","schema_id":"sender_name","samples_truncated":false,"samples":[{"datapoint_id":1357,"details":{"content":["Unregistered vendor"]}}]}]
- automation_disabledautomation is disabled due toqueuesettingslevel: annotationonlyoccurs whenautomation levelis set toneverorautomation_enabledqueue settingsisfalse
automation_disabled
- automation is disabled due toqueuesettings
- level: annotationonly
level: annotation
- occurs whenautomation levelis set toneverorautomation_enabledqueue settingsisfalse
never
automation_enabled
false
- is_duplicateannotation is a duplicate of another one (there exists a relation ofduplicatetype)
andautomate_duplicatequeue settingsis set tofalselevel: annotationonly
is_duplicate
- annotation is a duplicate of another one (there exists a relation ofduplicatetype)
andautomate_duplicatequeue settingsis set tofalse
duplicate
automate_duplicate
false
- level: annotationonly
level: annotation
- suggested_edit_presentthere is asuggested editby the AI engine andautomate_suggested_editqueue settingsis set tofalselevel: annotationonly
suggested_edit_present
- there is asuggested editby the AI engine andautomate_suggested_editqueue settingsis set tofalse
automate_suggested_edit
false
- level: annotationonly
level: annotation
- low_scoreAI confidence scoreis lower thanscore_thresholdset for givendatapointlevel: datapointonly
low_score
- AI confidence scoreis lower thanscore_thresholdset for givendatapoint
score_threshold
- level: datapointonly
level: datapoint
- failed_checksschema field constraint or connector validation failedonly forlevel: datapoint
failed_checks
- schema field constraint or connector validation failed
- only forlevel: datapoint
level: datapoint
- no_validation_sourcesvalidation source list was reset e.g. by hook, so automation was blockedonly forlevel: datapoint
no_validation_sources
- validation source list was reset e.g. by hook, so automation was blocked
- only forlevel: datapoint
level: datapoint
- error_messagefor bothlevels,annotationanddatapointerrortype messages received from connector
error_message
- for bothlevels,annotationanddatapoint
levels
annotation
datapoint
- errortype messages received from connector
error
- Delete recommendationbased on validation trigger match for the documentdelete_recommendation_filename,delete_recommendation_page_countlevel: annotationonlydeletion was recommended based on filename/page count condition of the triggerdelete_recommendation_fieldonly forlevel: datapointdeletion recommended based on a value of given field (defined in the condition of trigger)
- delete_recommendation_filename,delete_recommendation_page_countlevel: annotationonlydeletion was recommended based on filename/page count condition of the trigger
delete_recommendation_filename
delete_recommendation_page_count
- level: annotationonly
level: annotation
- deletion was recommended based on filename/page count condition of the trigger
- delete_recommendation_fieldonly forlevel: datapointdeletion recommended based on a value of given field (defined in the condition of trigger)
delete_recommendation_field
- only forlevel: datapoint
level: datapoint
- deletion recommended based on a value of given field (defined in the condition of trigger)
- extensionautomation blocker created by an extensionfor both levels -annotationanddatapoint
extension
- automation blocker created by an extension
- for both levels -annotationanddatapoint
annotation
datapoint

### List all automation blockers

List all automation blockers

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/automation_blockers'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/automation_blockers'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/automation_blockers/1","annotation":"https://<example>.rossum.app/api/v1/annotations/4","content":[{"level":"datapoint","type":"low_score","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"score":0.901,"threshold":0.975}}]},{"level":"datapoint","type":"failed_checks","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234,"details":{"validation":"bad"}}},{"level":"datapoint","type":"error_message","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234,"details":{"message_content":["Error 1","Error 2"]}}},{"level":"annotation","type":"suggested_edit_present"},{"level":"annotation","type":"is_duplicate"},{"level":"annotation","type":"error_message","details":{"message_content":["Error 1"]}}]}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/automation_blockers/1","annotation":"https://<example>.rossum.app/api/v1/annotations/4","content":[{"level":"datapoint","type":"low_score","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"score":0.901,"threshold":0.975}}]},{"level":"datapoint","type":"failed_checks","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234,"details":{"validation":"bad"}}},{"level":"datapoint","type":"error_message","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234,"details":{"message_content":["Error 1","Error 2"]}}},{"level":"annotation","type":"suggested_edit_present"},{"level":"annotation","type":"is_duplicate"},{"level":"annotation","type":"error_message","details":{"message_content":["Error 1"]}}]}]}
GET /v1/automation_blockers
GET /v1/automation_blockers
List all automation blocker objects.
Supported filters:annotation
annotation
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofautomation blockerobjects.

### Retrieve automation blocker

Get automation blocker12
12

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/automation_blockers/12'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/automation_blockers/12'

```
{"id":12,"url":"https://<example>.rossum.app/api/v1/automation_blockers/12","annotation":"https://<example>.rossum.app/api/v1/annotations/481","content":[{"level":"annotation","type":"automation_disabled"}]}
```

{"id":12,"url":"https://<example>.rossum.app/api/v1/automation_blockers/12","annotation":"https://<example>.rossum.app/api/v1/annotations/481","content":[{"level":"annotation","type":"automation_disabled"}]}
GET /v1/automation_blockers/{id}
GET /v1/automation_blockers/{id}

#### Response

Status200
200
Returnsautomation blockerobject.


## Connector

Example connector object

```
{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":"strict=true","client_ssl_certificate":"-----BEGIN CERTIFICATE-----\n...","authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":"strict=true","client_ssl_certificate":"-----BEGIN CERTIFICATE-----\n...","authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
A connector is an extension of Rossum that allows to validate and modify data
during validation and also export data to an external system. A connector
object is used to configure external or internal endpoint of such an extension
service. For more information seeExtensions.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the connectortruenamestringName of the connector (not visible in UI)urlURLURL of the connectortruequeueslist[URL]List of queues that use connector object.service_urlURLURL of the connector endpointparamsstringQuery params appended to the service_urlclient_ssl_certificatestringClient SSL certificate used to authenticate requests. Must be PEM encoded.client_ssl_keystringClient SSL key (write only). Must be PEM encoded. Key may not be encrypted.authorization_typestringsecret_keyString sent in HTTP headerAuthorizationcould be set tosecret_keyorBasic. For details seeConnector API.authorization_tokenstringToken sent to connector inAuthorizationheader to ensure connector was contacted by Rossum (displayed only toadminuser).asynchronousbooltrueAffects exporting: whentrue,confirmendpoint returns immediately and connector'ssaveendpoint is called asynchronously later on.metadataobject{}Client data.modified_byURLnullURL of the last connector modifiertruemodified_atdatetimenullDate of last modificationtrue
secret_key
Authorization
secret_key
Basic
Authorization
admin
true
true
save
{}
null
null

### List all connectors

List all connectors

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/connectors'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/connectors'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":"strict=true","client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":"strict=true","client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
GET /v1/connectors
GET /v1/connectors
Retrieve all connector objects.
Supported filters:id,name,service_url
id
name
service_url
Supported ordering:id,name,service_url
id
name
service_url
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofconnectorobjects.

### Create a new connector

Create new connector related to queue8199with endpoint URLhttps://myq.east-west-trading.com
8199
https://myq.east-west-trading.com

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Connector", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "service_url": "https://myq.east-west-trading.com", "authorization_token":"wuNg0OenyaeK4eenOovi7aiF"}'\'https://<example>.rossum.app/api/v1/connectors'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Connector", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "service_url": "https://myq.east-west-trading.com", "authorization_token":"wuNg0OenyaeK4eenOovi7aiF"}'\'https://<example>.rossum.app/api/v1/connectors'

```
{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
POST /v1/connectors
POST /v1/connectors
Create a new connector object.

#### Response

Status:201
201
Returns createdconnectorobject.

### Retrieve a connector

Get connector object1500
1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/connectors/1500'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/connectors/1500'

```
{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":null,"modified_at":null}
```

{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":null,"modified_at":null}
GET /v1/connectors/{id}
GET /v1/connectors/{id}
Get a connector object.

#### Response

Status:200
200
Returnsconnectorobject.

### Update a connector

Update connector object1500
1500

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Connector (stg)", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "service_url": "https://myq.stg.east-west-trading.com", "authorization_token":"wuNg0OenyaeK4eenOovi7aiF"} \
  'https://<example>.rossum.app/api/v1/connectors/1500'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Connector (stg)", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "service_url": "https://myq.stg.east-west-trading.com", "authorization_token":"wuNg0OenyaeK4eenOovi7aiF"} \
  'https://<example>.rossum.app/api/v1/connectors/1500'

```
{"id":1500,"name":"MyQ Connector (stg)","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.stg.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":1500,"name":"MyQ Connector (stg)","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.stg.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
PUT /v1/connectors/{id}
PUT /v1/connectors/{id}
Update connector object.

#### Response

Status:200
200
Returns updatedconnectorobject.

### Update part of a connector

Update connector URL of connector object1500
1500

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"service_url": "https://myq.stg2.east-west-trading.com"}'\'https://<example>.rossum.app/api/v1/connectors/1500'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"service_url": "https://myq.stg2.east-west-trading.com"}'\'https://<example>.rossum.app/api/v1/connectors/1500'

```
{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.stg2.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.stg2.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
PATCH /v1/connectors/{id}
PATCH /v1/connectors/{id}
Update part of connector object.

#### Response

Status:200
200
Returns updatedconnectorobject.

### Delete a connector

Delete connector1500
1500

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/connectors/1500'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/connectors/1500'
DELETE /v1/connectors/{id}
DELETE /v1/connectors/{id}
Delete connector object.

#### Response

Status:204
204


## Dedicated Engine

Example engine object

```
{"id":3000,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","queues":[]}
```

{"id":3000,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","queues":[]}
A Dedicated Engine object holds specification and a current state of training setup for a Dedicated Engine.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the enginetruenamestringName of the enginedescriptionstringDescription of the engineurlURLURL of the enginetruestatusenumdraftCurrent status of the engine,see belowtrueschemaurlnullRelateddedicated engine schema
draft

#### Dedicated Engine Status

Can be one ofdraft,schema_review,annotating_initial,annotating_review,annotating_training,training_started,training_finished, andretraining
draft
schema_review
annotating_initial
annotating_review
annotating_training
training_started
training_finished
retraining
Ifstatusis notdraft, the whole engine and its schema become read-only.
status
draft

### Request a new Dedicated Engine

Request a new Dedicated Engine using a form (multipart/form-data)

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fdocument_type="Custom invoice"-Fdocument_language="en-US"-Fvolume="9"\-Fsample_uploads=@document1.pdf-Fsample_uploads=@document2.pdf\'https://<example>.rossum.app/api/v1/dedicated_engines/request'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fdocument_type="Custom invoice"-Fdocument_language="en-US"-Fvolume="9"\-Fsample_uploads=@document1.pdf-Fsample_uploads=@document2.pdf\'https://<example>.rossum.app/api/v1/dedicated_engines/request'

```
{"id":3001,"url":"https://<example>.rossum.app/api/v1/dedicated_engines/3001","name":"Requested engine - Custom invoice","status":"sample_review","description":"AI engine trained to recognize customer-provided data for the customer's specific data capture requirements","schema":null}
```

{"id":3001,"url":"https://<example>.rossum.app/api/v1/dedicated_engines/3001","name":"Requested engine - Custom invoice","status":"sample_review","description":"AI engine trained to recognize customer-provided data for the customer's specific data capture requirements","schema":null}
POST /v1/dedicated_engines/request
POST /v1/dedicated_engines/request
Request training of a new Dedicated Engine
FieldTypeDescriptionRequireddocument_typestrType of the document the engine should predictTruedocument_languagestrLanguage of the documentsTruevolumeintEstimated volume per yearTruesample_uploadslist[FILE]Multiple sample files of the documents.

#### Response

Status:200
200
Returns createddedicated engineobject.

### List all dedicated engines

List all dedicated engines

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engines'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engines'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":3000,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":3000,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}]}
GET /v1/dedicated_engines
GET /v1/dedicated_engines
Retrieve all dedicated engine objects.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofdedicated engineobjects.

### Create a new dedicated engine

Create a new dedicated engine

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Dedicated engine 1", "schema": "https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6001"}'\'https://<example>.rossum.app/api/v1/dedicated_engines'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Dedicated engine 1", "schema": "https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6001"}'\'https://<example>.rossum.app/api/v1/dedicated_engines'

```
{"id":3001,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3001","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6001"}
```

{"id":3001,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3001","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6001"}
POST /v1/dedicated_engines
POST /v1/dedicated_engines
Create a new dedicated engine object.

#### Response

Status:201
201
Returns createddedicated engineobject.

### Retrieve a dedicated engine

Get dedicated engine object3000
3000

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'

```
{"id":3000,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}
```

{"id":3000,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}
GET /v1/dedicated_engines/{id}
GET /v1/dedicated_engines/{id}
Get a dedicated engine object.

#### Response

Status:200
200
Returnsdedicated engineobject.

### Update a dedicated engine

Update dedicated engine object3000
3000

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "New name", "schema": "https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "New name", "schema": "https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'

```
{"id":3000,"name":"New name","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}
```

{"id":3000,"name":"New name","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}
PUT /v1/dedicated_engines/{id}
PUT /v1/dedicated_engines/{id}
Update dedicated engine object.

#### Response

Status:200
200
Returns updateddedicated engineobject.

### Update part of a dedicated engine

Update content URL of dedicated engine object3000
3000

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "New name"}'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "New name"}'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'

```
{"id":3000,"name":"New name","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}
```

{"id":3000,"name":"New name","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}
PATCH /v1/dedicated_engines/{id}
PATCH /v1/dedicated_engines/{id}
Update part of a dedicated engine object.

#### Response

Status:200
200
Returns updateddedicated engineobject.

### Delete a dedicated engine

Delete dedicated engine3000
3000

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'
DELETE /v1/dedicated_engines/{id}
DELETE /v1/dedicated_engines/{id}
Delete dedicated engine object.

#### Response

Status:204
204


## Dedicated Engine Schema

Example dedicated engine schema object

```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":["https://<example>.rossum.app/api/v1/queues/123","https://<example>.rossum.app/api/v1/queues/200","https://<example>.rossum.app/api/v1/queues/321"],"fields":[{"category":"datapoint","engine_output_id":"document_id","type":"string","label":"Document ID","description":"Document number","trained":true,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/123","schema_id":"document_id"},{"queue":"https://<example>.rossum.app/api/v1/queues/200","schema_id":"custom_name_document_id"}]},{"category":"multivalue","children":{"category":"datapoint","engine_output_id":"order_id","type":"string","label":"Order Number","description":"Purchase order identification (Order Numbers not captured as 'sender_order_id')","trained":false,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/200","schema_id":"custom_name_order_id"},{"queue":"https://<example>.rossum.app/api/v1/queues/321","schema_id":"order_id"}]}},{"category":"multivalue","engine_output_id":"line_items","type":"grid","label":"Line Items","description":"Line item column types.","trained":true,"children":{"category":"tuple","children":[{"category":"datapoint","engine_output_id":"table_column_tax","type":"number","label":"Item Tax","description":"Tax amount for the line","trained":true,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/123","schema_id":"table_column_tax"},{"queue":"https://<example>.rossum.app/api/v1/queues/200","schema_id":"custom_table_column_tax"}]},{"category":"datapoint","engine_output_id":"table_column_rate","type":"number","label":"Item Rate","description":"Tax rate for the line item","trained":true,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/321","schema_id":"table_column_rate"}]}]}}]}}
```

{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":["https://<example>.rossum.app/api/v1/queues/123","https://<example>.rossum.app/api/v1/queues/200","https://<example>.rossum.app/api/v1/queues/321"],"fields":[{"category":"datapoint","engine_output_id":"document_id","type":"string","label":"Document ID","description":"Document number","trained":true,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/123","schema_id":"document_id"},{"queue":"https://<example>.rossum.app/api/v1/queues/200","schema_id":"custom_name_document_id"}]},{"category":"multivalue","children":{"category":"datapoint","engine_output_id":"order_id","type":"string","label":"Order Number","description":"Purchase order identification (Order Numbers not captured as 'sender_order_id')","trained":false,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/200","schema_id":"custom_name_order_id"},{"queue":"https://<example>.rossum.app/api/v1/queues/321","schema_id":"order_id"}]}},{"category":"multivalue","engine_output_id":"line_items","type":"grid","label":"Line Items","description":"Line item column types.","trained":true,"children":{"category":"tuple","children":[{"category":"datapoint","engine_output_id":"table_column_tax","type":"number","label":"Item Tax","description":"Tax amount for the line","trained":true,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/123","schema_id":"table_column_tax"},{"queue":"https://<example>.rossum.app/api/v1/queues/200","schema_id":"custom_table_column_tax"}]},{"category":"datapoint","engine_output_id":"table_column_rate","type":"number","label":"Item Rate","description":"Tax rate for the line item","trained":true,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/321","schema_id":"table_column_rate"}]}]}}]}}
An engine schema is an object which describes what fields are available in the engine. Do not confuse engine schema withDocument Schema.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the engine schematrueurlURLURL of the engine schematruecontentobjectSee below for description of the engine schema content
Schema can be edited only if its Dedicated Engine has statusdraft.
draft

#### Content structure

AttributeTypeDescriptiontraining_queueslist[URL]List of Queues that will be used for the training. Note that queues can't havedelete_afterfield set, otherwise a validation error is raised. (seequeue fields)fieldslist[object]Container for fields declarations. It may contain only objects of categorymultivalueordatapoint
delete_after
multivalue
datapoint
AttributeTypeDescriptionRead-onlycategorystringCategory of the object,multivalueengine_output_idstringUnique name of the newextracted fieldin the trained Dedicated EnginelabelstringUser-friendly label for an object, shown in the user interfacetrainedboolWhether the field was successfully trainedtruetypeenumType of the trained field. One of:gridandfreeform.descriptionstringDescription of field attributechildrenobjectObject specifying type of children. It may contain only objects with categoriestupleordatapoint.
multivalue
grid
freeform
tuple
datapoint
Multivalue objects withdatapointchildren do not haveengine_output_id,label,trained,type, ordescriptionattributes
datapoint
engine_output_id
label
trained
type
description
AttributeTypeDescriptioncategorystringCategory of the object,tuplechildrenlist[object]Array specifying objects that belong to a given tuple. It may contain only objects with categorydatapoint.
tuple
datapoint
AttributeTypeDescriptionRead-onlycategorystringCategory of the object,datapointengine_output_idstringName of the newextracted fieldin the trained Dedicated EnginelabelstringUser-friendly label for an object, shown in the user interfacetrainedboolWhether the field was successfully trainedtruetypeenumType of the trained field. One of:number,string,date, andenumdescriptionstringDescription of field attributesourceslist[Sources]Mapping describing the source Queues and their fields to train this field from
datapoint
number
string
date
enum
AttributeTypeDescriptionqueueURLQueue to map the field from. Only one Queue per engine output is allowedschema_idstringId of the field to map. The id must exist in the mapped Queue's schema

### Validate a dedicated engine schema

Validate content and integrity of dedicated engine schema object

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content":{"training_queues":["https://<example>.rossum.app/api/v1/queues/123"],"fields":[{"engine_output_id":"document_id","category":"datapoint","type":"string","label":"ID","description":"Document ID","sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/123","schema_id":"document_id"}]}]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/validate'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content":{"training_queues":["https://<example>.rossum.app/api/v1/queues/123"],"fields":[{"engine_output_id":"document_id","category":"datapoint","type":"string","label":"ID","description":"Document ID","sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/123","schema_id":"document_id"}]}]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/validate'
POST /v1/dedicated_engine_schemas/validate
POST /v1/dedicated_engine_schemas/validate
Validate dedicated engine schema object, check for errors. Additionally, to the basic checks done by the CRUD endpoints, this endpoint checks that:
- The declaredengine_output_ids are unique across the whole schema
engine_output_id
- The mapped Queue datapoints (viaschema_ids) are of the same type as the declaredtype
schema_id
type
- The mapped Queue datapoints ofenumtype have exactly the same option values declared
enum
- Differentshapes of datapointsare not mixed together
- The mapped Queue datapoints of Multivalue-Tuple fields are of the samegrid/freeformtype
grid
freeform
- When mapping to a single Multivalue-Tuple field, all the datapoints mapped from one Queue must come from a single tabular datapoint
- Multiple fields do not link to the same Queue Datapoint
- A mapped field either maps a Queue Datapoint withnull/emptyrir_field_namesor theengine_output_idmatches one of the mapped rir-namespacedrir_field_names(prefixed byrir:or nothing)
null
rir_field_names
engine_output_id
rir_field_names
rir:

#### Response

Status:200
200
Returns 200 and error description in case of validation failure.

### Predict a dedicated engine schema

Predict a dedicated engine schema

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"training_queues":["https://<example>.rossum.app/api/v1/queues/123", "https://<example>.rossum.app/api/v1/queues/200", "https://<example>.rossum.app/api/v1/queues/321"]}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/predict'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"training_queues":["https://<example>.rossum.app/api/v1/queues/123", "https://<example>.rossum.app/api/v1/queues/200", "https://<example>.rossum.app/api/v1/queues/321"]}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/predict'

```
{"content":{"training_queues":["https://<example>.rossum.app/api/v1/queues/123","https://<example>.rossum.app/api/v1/queues/200","https://<example>.rossum.app/api/v1/queues/321"],"fields":[...]}}
```

{"content":{"training_queues":["https://<example>.rossum.app/api/v1/queues/123","https://<example>.rossum.app/api/v1/queues/200","https://<example>.rossum.app/api/v1/queues/321"],"fields":[...]}}
POST /v1/dedicated_engine_schemas/predict
POST /v1/dedicated_engine_schemas/predict
Try to predict a dedicated engine schema based on the provided training queue's schemas. The predicted schema is not guaranteed to pass/v1/dedicated_engine_schemas/validatecheck, only the checks done on engine schema save
/v1/dedicated_engine_schemas/validate

#### Response

Status:200
200
Returns 200 and predicted dedicated engine schema

### List all dedicated engine schemas

List all dedicated engine schemas

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}]}
GET /v1/dedicated_engine_schemas
GET /v1/dedicated_engine_schemas
Retrieve all dedicated engine schema objects.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofdedicated engine schemaobjects.

### Create a new dedicated engine schema

Create a new dedicated engine schema

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": {"fields": [...], "training_queues": [...]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": {"fields": [...], "training_queues": [...]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas'

```
{"id":6001,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6001","content":{"training_queues":[...],"fields":[...]}}
```

{"id":6001,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6001","content":{"training_queues":[...],"fields":[...]}}
POST /v1/dedicated_engine_schemas
POST /v1/dedicated_engine_schemas
Create a new dedicated engine schema object.

#### Response

Status:201
201
Returns createddedicated engine schemaobject.

### Retrieve a dedicated engine schema

Retrieve dedicated engine schema object6000
6000

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'

```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
```

{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
GET /v1/dedicated_engine_schemas/{id}
GET /v1/dedicated_engine_schemas/{id}
Get a dedicated engine schema object.

#### Response

Status:200
200
Returnsdedicated engine schemaobject.

### Update a dedicated engine schema

Update dedicated engine schema object6000
6000

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": {"fields": [...], "training_queues": [...]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": {"fields": [...], "training_queues": [...]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'

```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
```

{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
PUT /v1/dedicated_engine_schemas/{id}
PUT /v1/dedicated_engine_schemas/{id}
Update dedicated engine schema object.

#### Response

Status:200
200
Returns updateddedicated engine schemaobject.

### Update part of a dedicated engine schema

Update content URL of dedicated engine schema object6000
6000

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": {"fields": [...], "training_queues": [...]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": {"fields": [...], "training_queues": [...]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'

```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
```

{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
PATCH /v1/dedicated_engine_schemas/{id}
PATCH /v1/dedicated_engine_schemas/{id}
Update part of a dedicated engine schema object.

#### Response

Status:200
200
Returns updateddedicated engine schemaobject.

### Delete a dedicated engine schema

Delete dedicated engine schema6000
6000

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'
DELETE /v1/dedicated_engine_schemas/{id}
DELETE /v1/dedicated_engine_schemas/{id}
Delete a dedicated engine schema object.

#### Response

Status:204
204


## Delete Recommendation

Example delete-recommendation object

```
{"id":1244,"enabled":true,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","triggers":["https://<example>.rossum.app/api/v1/triggers/500",]}
```

{"id":1244,"enabled":true,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","triggers":["https://<example>.rossum.app/api/v1/triggers/500",]}
AttributeTypeRequiredDescriptionRead-onlyidintegerId of the delete recommendation.trueenabledbooleanWhether the associated triggers' rules should be activeurlURLURL of the delete recommendation.trueorganizationURLURL of the associated organization.truequeueURLURL of the associated queue.triggersList[URL]URL of the associated triggers.
A Delete-recommendation is an object that binds together triggers that fire when a document meets a queue's
criteria for a deletion recommendation. Currently, only binding to a single trigger is supported.
The trigger bound to a DeleteRecommendation must belong to the same queue.

### List all delete recommendations

List all delete recommendations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/delete_recommendations'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/delete_recommendations'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","triggers":["https://<example>.rossum.app/api/v1/triggers/500",],},...]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","triggers":["https://<example>.rossum.app/api/v1/triggers/500",],},...]}
GET /v1/delete_recommendations
GET /v1/delete_recommendations
Retrieve all delete recommendations objects.

#### Supported filters

Delete recommendations currently support the following filters:
Filter nameTypeDescriptionqueueintegerFilter only delete recommendations associated with given queue id (or multiple ids).

#### Supported ordering

Delete recommendations currently support the following ordering:id,queue
id
queue
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofdelete recommendationobjects.

### Retrieve a delete recommendation

Get the delete recommendation object with ID1244
1244

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'

```
{"id":1244,"enabled":true,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","triggers":["https://<example>.rossum.app/api/v1/triggers/500",]}
```

{"id":1244,"enabled":true,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","triggers":["https://<example>.rossum.app/api/v1/triggers/500",]}
GET /v1/delete_recommendations/{id}
GET /v1/delete_recommendations/{id}
Get a delete recommendation object object.

#### Response

Status:200
200
Returns adelete recommendationobject.

### Create a delete recommendation

Create a new delete recommendation

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/132", "triggers": ["https://<example>.rossum.app/api/v1/triggers/5000"], "queue": "https://<example>.rossum.app/api/v1/queues/4857", "enabled": "True"}'\'https://<example>.rossum.app/api/v1/delete_recommendations/'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/132", "triggers": ["https://<example>.rossum.app/api/v1/triggers/5000"], "queue": "https://<example>.rossum.app/api/v1/queues/4857", "enabled": "True"}'\'https://<example>.rossum.app/api/v1/delete_recommendations/'

```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","enabled":true,"triggers":["https://<example>.rossum.app/api/v1/triggers/5000"]}
```

{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","enabled":true,"triggers":["https://<example>.rossum.app/api/v1/triggers/5000"]}
POST /v1/delete_recommendations/
POST /v1/delete_recommendations/
Create  a new delete recommendation

### Update a delete recommendation

Update the delete recommendation object with ID1244
1244

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"triggers": [], "enabled": "False"}'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"triggers": [], "enabled": "False"}'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'

```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","enabled":false,"triggers":[],...}
```

{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","enabled":false,"triggers":[],...}
PUT /v1/delete_recommendations/{id}
PUT /v1/delete_recommendations/{id}
Update a delete recommendation

### Update a part of a delete recommendation

Update flag enabled of delete recommendation object1244
1244

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"enabled": "False"}'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"enabled": "False"}'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'

```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","enabled":false,...}
```

{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","enabled":false,...}
PATCH /v1/delete_recommendations/{id}
PATCH /v1/delete_recommendations/{id}
Update a part of a delete recommendation

### Remove a delete recommendation

Remove the delete recommendation object 1244

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'
DELETE /v1/delete_recommendations/{id}
DELETE /v1/delete_recommendations/{id}
Remove a delete recommendation.


## Document

Example document object

```
{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628","s3_name":"272c2f01ae84a4e19a421cb432e490bb","parent":"https://<example>.rossum.app/api/v1/documents/203517","email":"https://<example>.rossum.app/api/v1/emails/987654","annotations":["https://<example>.rossum.app/api/v1/annotations/314528"],"mime_type":"application/pdf","creator":"https://<example>.rossum.app/api/v1/users/1","created_at":"2019-10-13T23:04:00.933658Z","arrived_at":"2019-10-13T23:04:00.933658Z","original_file_name":"test_invoice_1.pdf","content":"https://<example>.rossum.app/api/v1/documents/314628/content","attachment_status":null,"metadata":{}}
```

{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628","s3_name":"272c2f01ae84a4e19a421cb432e490bb","parent":"https://<example>.rossum.app/api/v1/documents/203517","email":"https://<example>.rossum.app/api/v1/emails/987654","annotations":["https://<example>.rossum.app/api/v1/annotations/314528"],"mime_type":"application/pdf","creator":"https://<example>.rossum.app/api/v1/users/1","created_at":"2019-10-13T23:04:00.933658Z","arrived_at":"2019-10-13T23:04:00.933658Z","original_file_name":"test_invoice_1.pdf","content":"https://<example>.rossum.app/api/v1/documents/314628/content","attachment_status":null,"metadata":{}}
A document object contains information about one input file. To create it, one can:
- Useuploadendpoint
Useuploadendpoint
- import document by email
import document by email
- create document via API
create document via API
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the documenttrueurlURLURL of the documenttrues3_namestringInternaltrueparentURLnullURL of the parent document (e.g. the zip file it was extracted from)trueemailURLURL of the email object that document was imported by (only for documents imported by email).trueannotationslist[URL]List of annotations related to the document. Usually there is only one annotation.truemime_typestringMIME type of the document (e.g.application/pdf)truecreatorURLUser that created the annotation.truecreated_atdatetimeTimestamp of document upload or incoming email attachment extraction.truearrived_atdatetime(Deprecated) Seecreated_attrueoriginal_file_namestringFile name of the attachment or upload.truecontentURLLink to the document's raw content (e.g. PDF file). May benullif there is no file associated.trueattachment_statusstringnullReason, why the Document got filtered out on Email ingestion. Seeattachment statustruemetadataobject{}Client data.
application/pdf
created_at
null
{}

#### Attachment status

Possible values:filtered_by_inbox_resolution,filtered_by_inbox_size,filtered_by_inbox_mime_type,filtered_by_inbox_file_name,filtered_by_hook_custom,filtered_by_queue_mime_type,hook_additional_file,filtered_by_insecure_mime_type,extracted_archive,failed_to_extract,processed,password_protected_archive,broken_imageandnull
filtered_by_inbox_resolution
filtered_by_inbox_size
filtered_by_inbox_mime_type
filtered_by_inbox_file_name
filtered_by_hook_custom
filtered_by_queue_mime_type
hook_additional_file
filtered_by_insecure_mime_type
extracted_archive
failed_to_extract
processed
password_protected_archive
broken_image
null

### List all documents

List all documents

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628",...},{"id":315609,"url":"https://<example>.rossum.app/api/v1/documents/315609",...}]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628",...},{"id":315609,"url":"https://<example>.rossum.app/api/v1/documents/315609",...}]}
GET /v1/documents
GET /v1/documents
Retrieve all document objects.
Supported filters:id,email,creator,arrived_at_before,arrived_at_after,created_at_before,created_at_after,original_file_name,attachment_status,parent
id
email
creator
arrived_at_before
arrived_at_after
created_at_before
created_at_after
original_file_name
attachment_status
parent
Supported ordering:id,arrived_at,created_at,original_file_name,mime_type,attachment_status
id
arrived_at
created_at
original_file_name
mime_type
attachment_status
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofdocumentobjects.

### Retrieve a document

Get document object314628
314628

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/314628'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/314628'

```
{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628",...}
```

{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628",...}
GET /v1/documents/{id}
GET /v1/documents/{id}
Get a document object.

#### Response

Status:200
200
Returnsdocumentobject.

### Create document

Create new document using a form (multipart/form-data)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/documents'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/documents'
Create new document by sending file in a request body

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/documents'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/documents'
Create new document by sending file in a request body (UTF-8 filename must be URL encoded)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H"Content-Disposition: attachment; filename*=utf-8''document%20%F0%9F%8E%81.pdf"--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/documents'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H"Content-Disposition: attachment; filename*=utf-8''document%20%F0%9F%8E%81.pdf"--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/documents'
Create documents using basic authentication

```
curl-u'east-west-trading-co@<example>.rossum.app:secret'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/documents'
```

curl-u'east-west-trading-co@<example>.rossum.app:secret'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/documents'
Create document with metadata and a parent document

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\-Fmetadata='{"project":"Market ABC"}'\-Fparent='https://<example>.rossum.app/api/v1/documents/456700'\'https://<example>.rossum.app/api/v1/documents'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\-Fmetadata='{"project":"Market ABC"}'\-Fparent='https://<example>.rossum.app/api/v1/documents/456700'\'https://<example>.rossum.app/api/v1/documents'

```
{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628",...}
```

{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628",...}
POST /v1/documents
POST /v1/documents
Create a new document object.
Use this API call to create a document without an annotation. Suitable for creating documents
for mime types that cannot be extracted by Rossum. Only one document can be created per request.
The supported mime types are the same as fordocument import.
Allowed attributes for creation request:
AttributeTypeDescriptioncontentbytesThe file to be uploaded.metadataobjectClient data.parentURLURL of the parent document (e.g. the original file based on which the uploaded content was created)

#### Response

Status:201
201
Returns createddocumentobject.

### Update part of a document

Update metadata of a document object314628
314628

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"metadata": {"translation_file_name": "Rechnung.pdf"}}'\'https://<example>.rossum.app/api/v1/documents/314628'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"metadata": {"translation_file_name": "Rechnung.pdf"}}'\'https://<example>.rossum.app/api/v1/documents/314628'

```
{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628","metadata":{"translation_file_name":"Rechnung.pdf"},...}
```

{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628","metadata":{"translation_file_name":"Rechnung.pdf"},...}
PATCH /v1/documents/{id}
PATCH /v1/documents/{id}
Update part of a document object.

### Document content

Download document original
To download multiple documents in one archive, refer todocuments downloadobject.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/314628/content'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/314628/content'
GET /v1/documents/{id}/content
GET /v1/documents/{id}/content
Get original document content (e.g. PDF file).

#### Response

Status:200
200
Returns original document file.

### Permanent URL

Download document original from a permanent URL

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/original/272c2f01ae84a4e19a421cb432e490bb'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/original/272c2f01ae84a4e19a421cb432e490bb'
GET /v1/original/272c2f01ae84a4e19a421cb432e490bb
GET /v1/original/272c2f01ae84a4e19a421cb432e490bb
Get original document content (e.g. PDF file).

#### Response

Status:200
200
Returns original document file.

### Delete a document

Delete document314628
314628

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/314628'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/314628'
DELETE /v1/documents/{id}
DELETE /v1/documents/{id}
Delete a document object from the database,
along with the related annotation and page objects,
but only if there are no datapoints associated to the annotation.
In order to reliably delete an annotation,mark it as deletedinstead.
This call also deletes the document data from Rossum systems.

#### Response

Status:204
204
Document successfully deleted.
Status:209
209
Document cannot be deleted due to existing datapoint references.


## Document Relation

Example document relation object

```
{"id":1,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124","https://<example>.rossum.app/api/v1/documents/125"],"url":"https://<example>.rossum.app/api/v1/document_relations/1"}
```

{"id":1,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124","https://<example>.rossum.app/api/v1/documents/125"],"url":"https://<example>.rossum.app/api/v1/document_relations/1"}
A document relation object introduces additional relations between annotations and documents. An annotation
can be related to one or more documents and it may belong to several such relations of different types at the
same time. These are additional to the main relation between the annotation and the document from which it was
created, seeannotation.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the document relationtruetype*stringexportType of relationship. Possible values areexport,einvoice. Seebelowkey*stringKey used to distinguish several relationships of the same type.annotation*URLAnnotationdocumentslist[URL]List of related documentsurlURLURL of the relationtrue
export
export
einvoice
* The combination oftype,keyandannotationattribute values must beunique.
type
key
annotation

#### Document relation types:

- export- Related documents are exports of the annotation data (e.g. in XML or JSON formats).
export
- einvoice- Related documents were created during import of an einvoice (e.g. validation report, visualisation, ...)
einvoice

### List all document relations

List all document relations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/document_relations'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/document_relations'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/456","https://<example>.rossum.app/api/v1/documents/457"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/456","https://<example>.rossum.app/api/v1/documents/457"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}]}
GET /v1/document_relations
GET /v1/document_relations
Retrieve all document relation objects.
Supported filters:
AttributeDescriptionidID of the document relation. Multiple values may be separated using a comma.typeRelationtype. Multiple values may be separated using a comma.annotationID of annotation. Multiple values may be separated using a comma.keyDocument relation keydocumentsID of related document. Multiple values may be separated using a comma.
Default ordering is byidin descending order. Supported other orderings are:id,type,annotation.
id
id
type
annotation
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofdocument relationobjects.

### Create a new document relation

Create a new document relation of type export

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "export", "annotation": "https://<example>.rossum.app/api/v1/annotations/123", "documents":'\'["https://<example>.rossum.app/api/v1/documents/124"]}'\'https://<example>.rossum.app/api/v1/document_relations'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "export", "annotation": "https://<example>.rossum.app/api/v1/annotations/123", "documents":'\'["https://<example>.rossum.app/api/v1/documents/124"]}'\'https://<example>.rossum.app/api/v1/document_relations'

```
{"id":789,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124"],"url":"https://<example>.rossum.app/api/v1/document_relations/789"}
```

{"id":789,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124"],"url":"https://<example>.rossum.app/api/v1/document_relations/789"}
POST /v1/document_relations
POST /v1/document_relations
Create a new document relation object.

#### Response

Status:201
201
Returns createddocument relationobject.

### Retrieve a document relation

Get document relation object with id1500
1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/document_relations/1500'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/document_relations/1500'

```
{"id":1500,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124","https://<example>.rossum.app/api/v1/documents/125"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}
```

{"id":1500,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124","https://<example>.rossum.app/api/v1/documents/125"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}
GET /v1/document_relations/{id}
GET /v1/document_relations/{id}
Get a document relation object.

#### Response

Status:200
200
Returnsdocument relationobject.

### Update a document relation

Update the document relation object with id1500
1500

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "export", "key": None, "annotation": "https://<example>.rossum.app/api/v1/annotations/123", "documents": ["https://<example>.rossum.app/api/v1/documents/124"]}'\'https://<example>.rossum.app/api/v1/document_relations/1500'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "export", "key": None, "annotation": "https://<example>.rossum.app/api/v1/annotations/123", "documents": ["https://<example>.rossum.app/api/v1/documents/124"]}'\'https://<example>.rossum.app/api/v1/document_relations/1500'

```
{"id":1500,"type":"edit","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}
```

{"id":1500,"type":"edit","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}
PUT /v1/document_relations/{id}
PUT /v1/document_relations/{id}
Update document relation object.

#### Response

Status:200
200
Returns updateddocument relationobject.

### Update part of a document relation

Update related documents on document relation object with ID1500
1500

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"documents": ["https://<example>.rossum.app/api/v1/documents/124", "https://<example>.rossum.app/api/v1/documents/125"]}'\'https://<example>.rossum.app/api/v1/document_relations/1500'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"documents": ["https://<example>.rossum.app/api/v1/documents/124", "https://<example>.rossum.app/api/v1/documents/125"]}'\'https://<example>.rossum.app/api/v1/document_relations/1500'

```
{"id":1500,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124","https://<example>.rossum.app/api/v1/documents/125"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}
```

{"id":1500,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124","https://<example>.rossum.app/api/v1/documents/125"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}
PATCH /v1/document_relations/{id}
PATCH /v1/document_relations/{id}
Update part of a document relation object.

#### Response

Status:200
200
Returns updateddocument_relationobject.

### Delete a document relation

Delete empty document relation1500
1500

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/document_relations/1500'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/document_relations/1500'
DELETE /v1/document_relations/{id}
DELETE /v1/document_relations/{id}
Delete a document relation object with empty related documents. If some documents still participate in the relation,
the caller must first delete those documents or update the document relation before deleting it.

#### Response

Status:204
204


## Documents Download

Example download object

```
{"id":105,"url":"https://<example>.rossum.app/api/v1/documents/downloads/105","file_name":"test_invoice_1.pdf","expires_at":"2023-09-13T23:04:00.933658Z","content":"https://<example>.rossum.app/api/v1/documents/downloads/105/content",}
```

{"id":105,"url":"https://<example>.rossum.app/api/v1/documents/downloads/105","file_name":"test_invoice_1.pdf","expires_at":"2023-09-13T23:04:00.933658Z","content":"https://<example>.rossum.app/api/v1/documents/downloads/105/content",}
Set of endpoints enabling download of multipledocumentsat once. The workflow of such action is
as follows:
- create a download object via POST on /documents/downloads. The response of the call will contain ataskURL.
create a download object via POST on /documents/downloads. The response of the call will contain ataskURL.
- call GET on the task URL. Watch the taskstatusto see when the task is ready.result_urlof a successful task will contain URL
to the download object.
call GET on the task URL. Watch the taskstatusto see when the task is ready.result_urlof a successful task will contain URL
to the download object.
status
result_url
- either call GET on the download object to get metadata about the object or call GET on the download object'scontentendpoint to
download the archive directly.
either call GET on the download object to get metadata about the object or call GET on the download object'scontentendpoint to
download the archive directly.
A download object contains information about a downloadable archive in.zipformat.
.zip
AttributeTypeDescriptionRead-onlyidintegerId of the download objecttrueurlURLURL of the download objecttrueexpires_atdatetimeTimestamp of a guaranteed availability of the download object and its content. Set to the archive creation time plus 2 hours. Expired downloads are being deleted periodically.truefile_namestringName of the archive to be downloaded.truecontentURLLink to the download's raw content. May benullif there is no archive associated yet.true
null

### Retrieve a download

GET /v1/documents/downloads/{id}
GET /v1/documents/downloads/{id}
Get a download object.

#### Response

Status:200
200
Returnsdownloadobject.

### Create new download

Create new download object

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"documents": ["https://<example>.rossum.app/api/v1/documents/123000", "https://<example>.rossum.app/api/v1/documents/123001"], "file_name": "monday_invoices.zip"}'\'https://<example>.rossum.app/api/v1/documents/downloads'
```

curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"documents": ["https://<example>.rossum.app/api/v1/documents/123000", "https://<example>.rossum.app/api/v1/documents/123001"], "file_name": "monday_invoices.zip"}'\'https://<example>.rossum.app/api/v1/documents/downloads'

```
{"url":"https://<example>.rossum.app/api/v1/tasks/301"}
```

{"url":"https://<example>.rossum.app/api/v1/tasks/301"}
POST /v1/documents/downloads
POST /v1/documents/downloads
Create a new download object.
ArgumentTypeRequiredDefaultDescriptiondocumentslist[URL]trueComma-separated list of document URLs to be included in the resulting downloadable archive. Max. 500 documents.file_namestringdocuments.zipThe filename of the resulting archive. Must include a.zipextension.typeenumdocumentOne of:documentandsource_document.zipbooleantrueUseapplication/zipto bundle the download contents.
documents.zip
.zip
document
document
source_document
application/zip
- Thezipvalue offalseis only applicable for single document downloads where thefile_nameif omitted in the
request is taken from the document being downloaded.
zip
false
file_name
- Thesource_documentmeans that for each of the documents the most distant non-emptyparentdocument is put into the download.
source_document
parent

#### Response

Status:202
202
The responseLocationheader provides the task url (same as in the JSON body of the response).
Location
Returns createdtaskobject.

### Retrieve download content

Download archive with original documents files

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/downloads/100/content'
```

curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/downloads/100/content'
GET /v1/documents/downloads/{id}/content
GET /v1/documents/downloads/{id}/content
Get archive with originaldocumentfiles.

#### Response

Status:200
200
Returns an archive with original document files.


## Email

Example email object

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/emails/1234","queue":"https://<example>.rossum.app/api/v1/queues/4321","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","documents":["https://<example>.rossum.app/api/v1/documents/5678"],"parent":"https://<example>.rossum.app/api/v1/emails/1230","children":["https://<example>.rossum.app/api/v1/emails/1244"],"created_at":"2021-03-26T14:31:46.993427Z","last_thread_email_created_at":"2021-03-27T14:29:48.665478Z","subject":"Some email subject","from":{"email":"company@east-west.com","name":"Company East"},"to":[{"email":"east-west-trading-co-a34f3a@<example>.rossum.app","name":"East West Trading"}],"cc":[],"bcc":[],"body_text_plain":"Some body","body_text_html":"<div dir=\"ltr\">Some body</div>","metadata":{},"type":"outgoing","annotation_counts":{"annotations":3,"annotations_processed":1,"annotations_purged":0,"annotations_unprocessed":1,"annotations_rejected":1},"annotations":["https://<example>.rossum.app/api/v1/annotations/1","https://<example>.rossum.app/api/v1/annotations/2","https://<example>.rossum.app/api/v1/annotations/4"],"related_annotations":[],"related_documents":["https://<example>.rossum.app/api/v1/documents/3"],"filtered_out_document_count":2,"labels":["rejected"]}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/emails/1234","queue":"https://<example>.rossum.app/api/v1/queues/4321","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","documents":["https://<example>.rossum.app/api/v1/documents/5678"],"parent":"https://<example>.rossum.app/api/v1/emails/1230","children":["https://<example>.rossum.app/api/v1/emails/1244"],"created_at":"2021-03-26T14:31:46.993427Z","last_thread_email_created_at":"2021-03-27T14:29:48.665478Z","subject":"Some email subject","from":{"email":"company@east-west.com","name":"Company East"},"to":[{"email":"east-west-trading-co-a34f3a@<example>.rossum.app","name":"East West Trading"}],"cc":[],"bcc":[],"body_text_plain":"Some body","body_text_html":"<div dir=\"ltr\">Some body</div>","metadata":{},"type":"outgoing","annotation_counts":{"annotations":3,"annotations_processed":1,"annotations_purged":0,"annotations_unprocessed":1,"annotations_rejected":1},"annotations":["https://<example>.rossum.app/api/v1/annotations/1","https://<example>.rossum.app/api/v1/annotations/2","https://<example>.rossum.app/api/v1/annotations/4"],"related_annotations":[],"related_documents":["https://<example>.rossum.app/api/v1/documents/3"],"filtered_out_document_count":2,"labels":["rejected"]}
An email object represents emails sent to Rossum inboxes.
AttributeTypeRequiredDescriptionRead-onlyidintegerId of the emailtrueurlURLURL of the emailtruequeueURLtrueURL of the associated queueinboxURLtrueURL of the associated inboxparentURLURL of the parent emailemail_threadURLURL of the associated email threadtruechildrenlist[URL]List of URLs of the children emailsdocumentslist[URL]List of documents attached to emailtruecreated_atdatetimeTimestamp of incoming emailtruelast_thread_email_created_atdatetime(Deprecated) Timestamp of the most recent email in this email threadtruesubjectstringEmail subjectfromemail_address_objectInformation about sender containing keysemailandname.truetolist[email_address_object]List that contains information about recipients.truecclist[email_address_object]List that contains information about recipients of carbon copy.truebcclist[email_address_object]List that contains information about recipients of blind carbon copy.truebody_text_plainstringPlain text email section (shortened to 4kB).body_text_htmlstringHTML email section (shortened to 4kB).metadataobjectClient data.typestringEmail type. Can beincomingoroutgoing.trueannotation_countsobjectThis attribute is intended forINTERNALuse only and may be changed in the future. Information about how many annotations were extracted from email attachments and in which state they currently aretrueannotationslist[URL]List of URLs of annotations that arrived via emailtruerelated_annotationslist[URL]List of URLs of annotations that are related to the email (e.g. rejected by that, added as attachment etc.)truerelated_documentslist[URL]List of URLs of documents related to the email (e.g. by forwarding email containing document as attachment etc.)truecreatorURLUser that have sent the email.Noneif email has been received via SMTPtruefiltered_out_document_countintegerThis attribute is intended forINTERNALuse only and may be changed in the future without notice. Number of documents automatically filtered out by Rossum smart inbox (this feature can be configured ininbox settings).truelabelslist[string]List of email labels. Possible values arerejection,automatic_rejection,rejected,automatic_status_changed_info,forwarded,replyfalsecontentURLURL of the emails contenttrue
email
name
incoming
outgoing
None
rejection
automatic_rejection
rejected
automatic_status_changed_info
forwarded
reply

#### Email address object

AttributeTypeDefaultDescriptionRequiredemailstringEmail addresstruenamestringName of the email recipient

#### Annotation counts object

This object stores numbers of annotations extracted from email attachments and their current status.
AttributeTypeDescriptionAnnotation statusannotationsintegerTotal number of annotationsAnyannotations_processedintegerNumber of processed annotationsexported,deleted,purged,splitannotations_purgedintegerNumber of purged annotationspurgedannotations_unprocessedintegerNumber of not yet processed annotationsimporting,failed_import,to_review,reviewing,confirmed,exporting,postponed,failed_exportannotations_rejectedintegerNumber of rejected annotationsrejectedrelated_annotationsintegerTotal number of related annotationsAny
exported
deleted
purged
split
purged
importing
failed_import
to_review
reviewing
confirmed
exporting
postponed
failed_export
rejected

#### Email labels

Email objects can have assigned any number of labels.
Label nameDescriptionrejectionOutgoing informative email sent by Rossum after email was manually rejected.automatic_rejectionInformative automatic email sent by Rossum when no document was extracted from incoming email.automatic_status_changed_infoInformative automatic email sent by Rossum about document status change.rejectedIncoming email rejected together with all attached documents.forwardedOutgoing email sent by forwarding other email.replyOutgoing email sent by replying to another email.

### List all emails

List all emails

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/emails'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/emails'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1234,"url":"https://<example>.rossum.app/api/v1/emails/1234","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","queue":"https://<example>.rossum.app/api/v1/queues/4321","documents":["https://<example>.rossum.app/api/v1/documents/5678"],...]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1234,"url":"https://<example>.rossum.app/api/v1/emails/1234","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","queue":"https://<example>.rossum.app/api/v1/queues/4321","documents":["https://<example>.rossum.app/api/v1/documents/5678"],...]}
GET /v1/emails
GET /v1/emails
Retrieve all emails objects.
Supported filters:id,created_at_before,created_at_after,subject,queue,inbox,documents,from__email,from__name,to,last_thread_email_created_at_before,last_thread_email_created_at_after,type,email_thread,has_documents
id
created_at_before
created_at_after
subject
queue
inbox
documents
from__email
from__name
to
last_thread_email_created_at_before
last_thread_email_created_at_after
type
email_thread
has_documents
Supported ordering:id,created_at,subject,queue,inbox,from__email,from__name,last_thread_email_created_at
id
created_at
subject
queue
inbox
from__email
from__name
last_thread_email_created_at
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofemailobjects.

### Retrieve an email

Get email object1244
1244

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/emails/1244'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/emails/1244'

```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/emails/1244","queue":"https://<example>.rossum.app/api/v1/queues/4321","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","documents":["https://<example>.rossum.app/api/v1/documents/5678"],"parent":"https://<example>.rossum.app/api/v1/emails/1230","children":[],"arrived_at":"2021-03-26T14:31:46.993427Z","last_thread_email_created_at":"2021-03-27T14:29:48.665478Z","subject":"Some email subject","from":{"email":"company@east-west.com"},"to":[{"email":"east-west-trading-co-a34f3a@<example>.rossum.app"}],"cc":[],"bcc":[],"body_text_plain":"","body_text_html":"","metadata":{},"type":"outgoing","labels":[],...}
```

{"id":1244,"url":"https://<example>.rossum.app/api/v1/emails/1244","queue":"https://<example>.rossum.app/api/v1/queues/4321","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","documents":["https://<example>.rossum.app/api/v1/documents/5678"],"parent":"https://<example>.rossum.app/api/v1/emails/1230","children":[],"arrived_at":"2021-03-26T14:31:46.993427Z","last_thread_email_created_at":"2021-03-27T14:29:48.665478Z","subject":"Some email subject","from":{"email":"company@east-west.com"},"to":[{"email":"east-west-trading-co-a34f3a@<example>.rossum.app"}],"cc":[],"bcc":[],"body_text_plain":"","body_text_html":"","metadata":{},"type":"outgoing","labels":[],...}
GET /v1/emails/{id}
GET /v1/emails/{id}
Get an email object.

#### Response

Status:200
200
Returnsemailobject.

### Update an email

Update email object1244
1244

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "inbox": "https://<example>.rossum.app/api/v1/inboxes/8236", "subject": "Some subject", "to": [{"email": "jack@east-west-trading.com"}]}'\'https://<example>.rossum.app/api/v1/emails/1244'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "inbox": "https://<example>.rossum.app/api/v1/inboxes/8236", "subject": "Some subject", "to": [{"email": "jack@east-west-trading.com"}]}'\'https://<example>.rossum.app/api/v1/emails/1244'

```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/emails/1244","queue":"https://<example>.rossum.app/api/v1/queues/4321","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","documents":[],"parent":null,"children":[],"arrived_at":"2021-03-26T14:31:46.993427Z","last_thread_email_created_at":"2021-03-27T14:29:48.665478Z","subject":"Some subject","from":null,"to":[{"email":"jack@east-west-trading.com"}],"body_text_plain":"","body_text_html":"","metadata":{},"type":"outgoing","labels":[],...}
```

{"id":1244,"url":"https://<example>.rossum.app/api/v1/emails/1244","queue":"https://<example>.rossum.app/api/v1/queues/4321","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","documents":[],"parent":null,"children":[],"arrived_at":"2021-03-26T14:31:46.993427Z","last_thread_email_created_at":"2021-03-27T14:29:48.665478Z","subject":"Some subject","from":null,"to":[{"email":"jack@east-west-trading.com"}],"body_text_plain":"","body_text_html":"","metadata":{},"type":"outgoing","labels":[],...}
PUT /v1/emails/{id}
PUT /v1/emails/{id}
Update email object.

#### Response

Status:200
200
Returns updatedemailobject.

### Update part of an email

Update subject of email object1244
1244

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"subject": "Some subject"}'\'https://<example>.rossum.app/api/v1/emails/1244'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"subject": "Some subject"}'\'https://<example>.rossum.app/api/v1/emails/1244'

```
{"id":1244,"subject":"Some subject",...}
```

{"id":1244,"subject":"Some subject",...}
PATCH /v1/emails/{id}
PATCH /v1/emails/{id}
Update part of email object.

#### Response

Status:200
200
Returns updatedemailobject.

### Import email

Import email using a form (multipart/form-data)

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fraw_message=@email.eml-Frecipient="east-west-trading-co-a34f3a@<example>.rossum.app"\'https://<example>.rossum.app/api/v1/emails/import'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fraw_message=@email.eml-Frecipient="east-west-trading-co-a34f3a@<example>.rossum.app"\'https://<example>.rossum.app/api/v1/emails/import'
Import email with metadata and values

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fraw_message=@email.eml\-Frecipient="east-west-trading-co-a34f3a@<example>.rossum.app"\-F'metadata={"source":"rossum","batch_id":"12345"}'\-F'values={"emails_import:customer_id":"CUST-001","emails_import:order_number":"ORD-456"}'\'https://<example>.rossum.app/api/v1/emails/import'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fraw_message=@email.eml\-Frecipient="east-west-trading-co-a34f3a@<example>.rossum.app"\-F'metadata={"source":"rossum","batch_id":"12345"}'\-F'values={"emails_import:customer_id":"CUST-001","emails_import:order_number":"ORD-456"}'\'https://<example>.rossum.app/api/v1/emails/import'

```
{"url":"https://<example>.rossum.app/api/v1/tasks/456575"}
```

{"url":"https://<example>.rossum.app/api/v1/tasks/456575"}
POST /v1/emails/import
POST /v1/emails/import
Import an email as raw data. Calling this endpoint starts an asynchronous process of creating
an email object and importing its contents to the specified recipient inbox in Rossum. This endpoint
can be used only byadminandorganization_group_adminroles and email can be imported only to
inboxes within the organization. The caller of this endpoint will be specified as thecreatorof the email.
The email sender specified in thefromheader will still receive any automated notifications targeted to the
email recipients.
admin
organization_group_admin
creator
from
KeyTypeRequiredDescriptionraw_messagebytestrueRaw email data.recipientstringtrueEmail address of the inbox where the email will be imported.metadataobjectfalseJSON object with metadata to be set on created annotations.valuesobjectfalseJSON object with values to be set on created annotations. All keys must start with theemails_import:prefix (e.g.,emails_import:customer_id).
emails_import:
emails_import:customer_id

#### Response

Status:202
202
Import email endpoint is asynchronous and response contains created task url. Further information about
the import status may be acquired by retrieving the email object or the task (for more information, please refer totask)
Example import response

```
{
  "url": "https://example.rossum.app/api/v1/tasks/456575"
}
```


### Send email

Send email

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"to": [{"email": "jack@east-west-trading.com"}], "queue": "https://<example>.rossum.app/api/v1/queues/145300", "template_values": {"subject": "Some subject", "message": "<b>Hello!</b>"}}'\'https://<example>.rossum.app/api/v1/emails/send'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"to": [{"email": "jack@east-west-trading.com"}], "queue": "https://<example>.rossum.app/api/v1/queues/145300", "template_values": {"subject": "Some subject", "message": "<b>Hello!</b>"}}'\'https://<example>.rossum.app/api/v1/emails/send'
POST /v1/emails/send
POST /v1/emails/send
Send email to specified recipients. The number of emails that can be sent is limited (10 for trials accounts).
KeyTypeRequiredDescriptionto*list[email_address_object]List that contains information about recipients.cc*list[email_address_object]List that contains information about recipients of carbon copy.bcc*list[email_address_object]List that contains information about recipients of blind carbon copy.template_valuesobjectfalseValues to fill in the email template, it should always containsubjectandmessagekeys. See below for description.queueURLtrueLink to email-related queue.related_annotationslist[URL]falseList of links to email-related annotations.related_documentslist[URL]falseList of URLs to email-related documents (on the top ofrelated_annotationsdocuments which are linked automatically).attachmentsobjectfalseKeys are attachment types (currently onlydocumentskey is supported), value is list of URL.parent_emailURLfalseLink to parent email.reset_related_annotations_email_threadboolfalseUpdate related annotations, so that theiremail threadmatches the one of the email object created.labelslist[string]falseList ofemail labels.email_templateURLfalseLink to the email template that was used for the email creation. If specified, the email will be included in theemail templates stats.
subject
message
related_annotations
documents
*At least one email into,cc,bccmust be filled. The total number of recipients (to,ccandbcctogether) cannot exceed 40.
to
cc
bcc
to
cc
bcc
If the related annotation hasnullemail thread, it will be linked to the email thread related to the email created.
null
emailobject consists of names and email addresses:
email
KeyTypeRequiredDescriptionemailemailtrueEmail address, e.g.john.doe@example.comnamestringfalseName related to the email, e.g.John Doe
john.doe@example.com
John Doe

#### Template values

Objecttemplate_valuesis used to create an outgoing email. Keysubjectis used to fill an email subject andmessageis used to fill a body of the email (it may contain a subset of html).
Values may contain other placeholders that are either built-in (see below) or specified in thetemplate_valuesobject as well. For placeholders referring to annotations, the annotations fromrelated_annotationsattribute are used for filling in correct values.
template_values
subject
message
template_values
related_annotations
Example of template_values

```
{..."template_values":{"subject":"Document processed","message":"<p>The document was processed.<br>{{user_name}}<br>Additional notes: {{note}}</p>","note":"No issues found"}...}
```

{..."template_values":{"subject":"Document processed","message":"<p>The document was processed.<br>{{user_name}}<br>Additional notes: {{note}}</p>","note":"No issues found"}...}
PlaceholderDescriptionCan be used in automationorganization_nameName of the organization.Trueapp_urlApp root urlTrueuser_nameUsername of the user sending the email.Falsecurrent_user_fullnameFull name of user sending the email.Falsecurrent_user_emailEmail address of the user sending the email.Falseparent_email_subjectSubject of the email we are replying to.Truesender_emailEmail address of the author of the incoming email.Trueannotation.document.original_file_nameFilenames of the documents belonging to the related annotation(s)Trueannotation.content.value.{schema_id}Content value of datapoints from email related annotation(s)Trueannotation.idIds of the related annotation(s)Trueannotation.urlUrls of the related annotation(s)Trueannotation.assignee_emailEmails of the assigned users to the related annotation(s)True
Example request data

```
{"to":[{"name":"John Doe","email":"john.doe@rossum.ai"}],"template_values":{"subject":"Rejected!: {{parent_email_subject}}","message":"<p>Dear user,<br>Error occurred!<br><br>Note: {{rejection_note}}. Occurred on your document issued at {{ annotation.content.value.date_issue }}.<br>Yours, Rossum</p>","rejection_note":"There is no invoice id!"},"annotations":["https://<example>.rossum.app/api/v1/annotations/123"],"attachments":{"documents":["https://<example>.rossum.app/api/v1/documents/123"]}}
```

{"to":[{"name":"John Doe","email":"john.doe@rossum.ai"}],"template_values":{"subject":"Rejected!: {{parent_email_subject}}","message":"<p>Dear user,<br>Error occurred!<br><br>Note: {{rejection_note}}. Occurred on your document issued at {{ annotation.content.value.date_issue }}.<br>Yours, Rossum</p>","rejection_note":"There is no invoice id!"},"annotations":["https://<example>.rossum.app/api/v1/annotations/123"],"attachments":{"documents":["https://<example>.rossum.app/api/v1/documents/123"]}}

#### Response

Status:200
200
Returns created email link.

### Get email counts

Get email counts

```
curl-XGET-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/emails/counts'
```

curl-XGET-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/emails/counts'

```
{"incoming":{"total":12,"no_documents":5,"recent_with_no_documents_not_replied":2,"rejected":1,"recent_filtered_out_documents":2}}
```

{"incoming":{"total":12,"no_documents":5,"recent_with_no_documents_not_replied":2,"rejected":1,"recent_filtered_out_documents":2}}
GET /v1/emails/counts
GET /v1/emails/counts
Retrieve counts of emails grouped based on status of extracted annotations.
Supports the same filters aslist emailsendpoint.

#### Response

Status:200
200
Returns object which under theincomingkey contains object with email counts computed based on the status of extracted documents
incoming
AttributeTypeDescriptiontotalintegerTotal number of emailsno_documentsintegerNumber of emails containing no attachment which was processed by Rossumrecent_with_no_documents_not_repliedintegerNumber of emails arrived in the last 14 days with no attachment processed by Rossum, not withrejectedlabel and without any reply (i. e. email has no relatedchildrenemails - seeemail docs).rejectedintegerNumber of emails containing at least one document inrejectedstatus (seedocument lifecycle) or withrejectedlabel.recent_with_filtered_out_documentsintegerNumber of emails arrived in the last 14 days containing one or more automatically rejected attachment by Rossum smart inbox (rules for email attachment filtering is definedhere).
rejected
children
rejected
rejected

### Email content

GET /emails/<id>/content
GET /emails/<id>/content
Retrieve content of email.

#### Response

Status:200
200

### Email notifications management

Unsubscribe from automatic email notifications

```
curl-XGET'https://<example>.rossum.app/api/v1/emails/subscription?content=eyJldmVudCI6ImRvY3VtZW50X3JlY2VpdmVkIiwiZW1haWwiOiJqaXJpLmJhdWVyQHJvc3N1bS5haSIsIm9yZ2FuaXphdGlvbiI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODAwMC92MS9vcmdhbml6YXRpb25zLzEifQ&signature=LhgMR01vQ9NAsvAtOKifZpaYBi20vkhOK-Cm7HT1Cqs&subscribe=false'
```

curl-XGET'https://<example>.rossum.app/api/v1/emails/subscription?content=eyJldmVudCI6ImRvY3VtZW50X3JlY2VpdmVkIiwiZW1haWwiOiJqaXJpLmJhdWVyQHJvc3N1bS5haSIsIm9yZ2FuaXphdGlvbiI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODAwMC92MS9vcmdhbml6YXRpb25zLzEifQ&signature=LhgMR01vQ9NAsvAtOKifZpaYBi20vkhOK-Cm7HT1Cqs&subscribe=false'

```
<!DOCTYPE html>...</html>
```

<!DOCTYPE html>...</html>
GET /v1/emails/subscription?subscribe=false
GET /v1/emails/subscription?subscribe=false
Enable or disable subscription to automatic email notifications sent by Rossum.
Query parameterTypeDefaultRequiredDescriptionsignaturestringtrueSignature used to sign the content (generated by our backend).contentstringtrueSigned content of the payload (generated by our backend).subscribebooleantruefalseDesignates whether the subscription is enabled or disabled.

#### Response

Status:200
200
Renders HTML page.

### Email tracking events

Email tracking events

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"payload": "ORSXG5DTFVZHVZLSFZQG6Y3BNQ5DC===", "signature": "nGoqalaYlSMFiCPmJDPWaiN3FLEm_cPbxA4mrgqodpk", "link": "https://rossum.ai", "event": "click"}'\'https://<example>.rossum.app/api/v1/email_tracking_events'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"payload": "ORSXG5DTFVZHVZLSFZQG6Y3BNQ5DC===", "signature": "nGoqalaYlSMFiCPmJDPWaiN3FLEm_cPbxA4mrgqodpk", "link": "https://rossum.ai", "event": "click"}'\'https://<example>.rossum.app/api/v1/email_tracking_events'
POST /v1/email_tracking_events
POST /v1/email_tracking_events
Rossum has the ability to track email events:send,delivery,open,click,bouncefor sent emails.
send
delivery
open
click
bounce
KeyTypeRequiredDescriptionpayloadstringTrueEncrypted email, domain and organization ID.eventstringTrueActions performed on the sent email: bounce, send, delivery, open, click.linkURLFalseThe link from the email body that the user clicked on.signaturestringTrueSignature used to sign the encrypted domain (generated by our backend).

#### Response

Status:201
201


## Email Template

Example email template object

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","triggers":["https://<example>.rossum.app/api/v1/triggers/500","https://<example>.rossum.app/api/v1/triggers/600"],"type":"custom","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","automate":true}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","triggers":["https://<example>.rossum.app/api/v1/triggers/500","https://<example>.rossum.app/api/v1/triggers/600"],"type":"custom","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","automate":true}
An email template object represents templates one can choose from when sending an email from Rossum.
AttributeTypeDefaultRequiredDescriptionRead-onlyidintegerId of the email templatetrueurlURLURL of the email templatenamestringtrueName of the email templatequeueURLtrueURL of the associated queueorganizationURLURL of the associated organizationtriggerslist[URL]URLs of the linked triggers.Read moretypestringcustomType of the email template (seeemail template types)subjectstring""Email subjectmessagestring""HTML subset of text email sectionenabledbooltrue(Deprecated) UseautomateinsteadautomatebooltrueTrue if user wants to send email automatically on the action, seetypesto*list[email_address_object][]List that contains information about recipients.cc*list[email_address_object][]List that contains information about recipients of carbon copy.bcc*list[email_address_object][]List that contains information about recipients of blind carbon copy.
custom
""
""
automate
*The total number of recipients (to,ccandbcctogether) cannot exceed 40.
to
cc
bcc

#### Email Template Types

Email Template objects can have one of the following types. Only templates with typesrejectionandcustomcan be manually created and deleted.
rejection
custom
Template type nameDescriptionrejectionTemplate for a rejection emailrejection_defaultDefault template for a rejection emailemail_with_no_processable_attachmentsTemplate for a reply to an email with no attachmentscustomCustom email template

#### Default Email templates

Every newly created queue triggers a creation of five default email templates with default messages and subjects.

```
[{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"Annotation status change - confirmed","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Verified documents: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Your documents have been checked by annotator.<br><br>{{ document_list }}<br><br>Regards</p>","type":"custom","triggers":["https://<example>.rossum.app/api/v1/triggers/456"],"automate":false,"to":[{"email":"{{sender_email}}"}]},{"id":1235,"url":"https://<example>.rossum.app/api/v1/email_templates/1235","name":"Annotation status change - exported","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Documents exported: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Your documents have been successfully exported.<br><br>{{ document_list }}<br><br>Regards</p>","type":"custom","triggers":["https://<example>.rossum.app/api/v1/triggers/457"],"automate":false,"to":[{"email":"{{sender_email}}"}]},{"id":1236,"url":"https://<example>.rossum.app/api/v1/email_templates/1236","name":"Annotation status change - received","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Documents received: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Your documents have been successfully received.<br><br>{{ document_list }}<br><br>Regards</p>","type":"custom","triggers":["https://<example>.rossum.app/api/v1/triggers/458"],"automate":false,"to":[{"email":"{{sender_email}}"}]},{"id":1237,"url":"https://<example>.rossum.app/api/v1/email_templates/1237","name":"Default rejection template","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Rejected document {{parent_email_subject}}","message":"<p>Dear sender,<br><br>The attached document has been rejected.<br><br><br>Best regards,<br>{{ user_name }}</p>","type":"rejection_default","triggers":[],"automate":true,"to":[{"email":"{{sender_email}}"}]},{"id":1238,"url":"https://<example>.rossum.app/api/v1/email_templates/1238","name":"Email with no processable attachments","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"No processable documents: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Unfortunately, we have not received any document in the email that we can process. Please send a corrected version if appropriate.<br><br>Regards</p>","type":"email_with_no_processable_attachments","triggers":["https://<example>.rossum.app/api/v1/triggers/459"],"automate":false,"to":[{"email":"{{sender_email}}"}]}]
```

[{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"Annotation status change - confirmed","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Verified documents: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Your documents have been checked by annotator.<br><br>{{ document_list }}<br><br>Regards</p>","type":"custom","triggers":["https://<example>.rossum.app/api/v1/triggers/456"],"automate":false,"to":[{"email":"{{sender_email}}"}]},{"id":1235,"url":"https://<example>.rossum.app/api/v1/email_templates/1235","name":"Annotation status change - exported","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Documents exported: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Your documents have been successfully exported.<br><br>{{ document_list }}<br><br>Regards</p>","type":"custom","triggers":["https://<example>.rossum.app/api/v1/triggers/457"],"automate":false,"to":[{"email":"{{sender_email}}"}]},{"id":1236,"url":"https://<example>.rossum.app/api/v1/email_templates/1236","name":"Annotation status change - received","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Documents received: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Your documents have been successfully received.<br><br>{{ document_list }}<br><br>Regards</p>","type":"custom","triggers":["https://<example>.rossum.app/api/v1/triggers/458"],"automate":false,"to":[{"email":"{{sender_email}}"}]},{"id":1237,"url":"https://<example>.rossum.app/api/v1/email_templates/1237","name":"Default rejection template","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Rejected document {{parent_email_subject}}","message":"<p>Dear sender,<br><br>The attached document has been rejected.<br><br><br>Best regards,<br>{{ user_name }}</p>","type":"rejection_default","triggers":[],"automate":true,"to":[{"email":"{{sender_email}}"}]},{"id":1238,"url":"https://<example>.rossum.app/api/v1/email_templates/1238","name":"Email with no processable attachments","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"No processable documents: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Unfortunately, we have not received any document in the email that we can process. Please send a corrected version if appropriate.<br><br>Regards</p>","type":"email_with_no_processable_attachments","triggers":["https://<example>.rossum.app/api/v1/triggers/459"],"automate":false,"to":[{"email":"{{sender_email}}"}]}]

#### Email template rendering

Email templates supportDjango Template Variables.
Please note that only simple variables are supported. Filters and the.lookup are not. A template such as:
.

```
{% if subject %}
  The subject is {{ subject }}.
  {% endif %}
  The message is {{ message|lower }}.
```

with template settings such as:

```
{'subject': 'Hello', 'message': 'World'}
```

will render as:

```
{% if subject %}
  The subject is Hello.
  {% endif %}
  The message is .
```


### List all email templates

List all email templates

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_templates'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_templates'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","type":"custom","automate":true}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","type":"custom","automate":true}]}
GET /v1/email_templates
GET /v1/email_templates
Retrieve all email template objects.
Supported filters:id,queue,type,name
id
queue
type
name
Supported ordering:id,name
id
name
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofemail templateobjects.

### Create new email template object

Create new email template in queue4321
4321

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "name": "My Email Template", "subject": "My Email Template Subject", "message": "<p>My Email Template Message</p>", "type": "custom"}'\'https://<example>.rossum.app/api/v1/email_templates'
```

curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "name": "My Email Template", "subject": "My Email Template Subject", "message": "<p>My Email Template Message</p>", "type": "custom"}'\'https://<example>.rossum.app/api/v1/email_templates'

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","type":"custom"}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","type":"custom"}
POST /v1/email_templates
POST /v1/email_templates
Create new email template object.

#### Response

Status:201
201
Returns newemail templateobject.

### Retrieve an email template object

Get email template object1234
1234

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_templates/1234'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_templates/1234'

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","type":"custom","automate":true}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","type":"custom","automate":true}
GET /v1/email_templates/{id}
GET /v1/email_templates/{id}
Get an email template object.

#### Response

Status:200
200
Returnsemail templateobject.

### Update an email template

Update email template object1234
1234

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "subject": "Some new subject"}'\'https://<example>.rossum.app/api/v1/email_templates/1234'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "subject": "Some new subject"}'\'https://<example>.rossum.app/api/v1/email_templates/1234'

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"Some new subject","message":"<p>My Email Template Message</p>","type":"custom","automate":true}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"Some new subject","message":"<p>My Email Template Message</p>","type":"custom","automate":true}
PUT /v1/email_templates/{id}
PUT /v1/email_templates/{id}
Update email template object.

#### Response

Status:200
200
Returns updatedemail templateobject.

### Update part of an email template

Update subject of email template object1234
1234

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"subject": "Some new subject"}'\'https://<example>.rossum.app/api/v1/email_templates/1234'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"subject": "Some new subject"}'\'https://<example>.rossum.app/api/v1/email_templates/1234'

```
{"id":1234,"subject":"Some new subject",...}
```

{"id":1234,"subject":"Some new subject",...}
PATCH /v1/email_templates/{id}
PATCH /v1/email_templates/{id}
Update part of an email template object.

#### Response

Status:200
200
Returns updatedemail templateobject.

### Delete an email template

Delete email template object1234
1234

```
curl-XDELETE'https://<example>.rossum.app/api/v1/email_templates/1234'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
```

curl-XDELETE'https://<example>.rossum.app/api/v1/email_templates/1234'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
DELETE /v1/email_templates/{id}
DELETE /v1/email_templates/{id}
Delete an email template object.

#### Response

Status:204
204

### Get email templates stats

Get stats for all email templates from queue with id478
478

```
curl-XGET'https://<example>.rossum.app/api/v1/email_templates/stats?queue=478'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
```

curl-XGET'https://<example>.rossum.app/api/v1/email_templates/stats?queue=478'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'

```
{"pagination":{"total":6,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/email_templates/2","manual_count":12,"automated_count":190},{"url":"https://<example>.rossum.app/api/v1/email_templates/3","manual_count":87,"automated_count":0},...]}
```

{"pagination":{"total":6,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/email_templates/2","manual_count":12,"automated_count":190},{"url":"https://<example>.rossum.app/api/v1/email_templates/3","manual_count":87,"automated_count":0},...]}
GET /v1/email_templates/stats
GET /v1/email_templates/stats
Get stats for email templates.

#### Response

Status:200
200
Returns paginated response with a list of following objects
AttributeTypeDescriptionurlURLLink of the email template.manual_countintegerNumber of manually sent emails in the last 90 days based on given email template.automated_countintegerNumber of automatically sent emails in the last 90 days based on given email template.
Supports the same filters aslist email templatesendpoint.

### Render email template

Render email template221
221

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"parent_email": "https://<example>.rossum.app/api/v1/emails/1234", "document_list": ["https://<example>.rossum.app/api/v1/documents/2314"], "to": [{"email": "{{ current_user_email }}"}]}'\'https://<example>.rossum.app/api/v1/email_templates/221/render'
```

curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"parent_email": "https://<example>.rossum.app/api/v1/emails/1234", "document_list": ["https://<example>.rossum.app/api/v1/documents/2314"], "to": [{"email": "{{ current_user_email }}"}]}'\'https://<example>.rossum.app/api/v1/email_templates/221/render'

```
{"to":[{"email":"satisfied.customer@rossum.ai"}],"cc":[],"bcc":[],"subject":"My Email Template Subject: Rendered Parent Email Subject","message":"<p>My Email Template Message from user@example.com</p>"}
```

{"to":[{"email":"satisfied.customer@rossum.ai"}],"cc":[],"bcc":[],"subject":"My Email Template Subject: Rendered Parent Email Subject","message":"<p>My Email Template Message from user@example.com</p>"}
POST /v1/email_templates/{id}/render
POST /v1/email_templates/{id}/render
The rendered email template can be requested via therenderendpoint with the following attributes:
render
AttributeTypeDefaultRequiredDescriptionto*list[email_address_object][]falseList that contains information about recipients to be rendered.cc*list[email_address_object][]falseList that contains information about recipients of carbon copy to be rendered.bcc*list[email_address_object][]falseList that contains information about recipients of blind carbon copy to be rendered.parent_emailURLfalseLink toparent_email.document_listlist[URL][]falseList ofdocument's URLs to simulate sending of documents over email into Rossumannotation_listlist[URL][]falseList ofannotation's URLs to use for rendering values for annotation.content placeholderstemplate_valuesobject{}falseValues to fill in the email template.Read more.
[]
[]
[]
[]
[]
{}
*The total number of recipients (to,ccandbcctogether) cannot exceed 40.
Inside theto,ccandbccattributes template variables can be used instead of the email field of theemail_address_object. See thelist of built-in placeholdersfor available variables.
to
cc
bcc
to
cc
bcc

#### Response

Status:200
200
Returns rendered message and subject of an email template
AttributeTypeDescriptiontolist[email_address_object]List that contains rendered information about recipients.cclist[email_address_object]List that contains rendered information about recipients of carbon copy.bcclist[email_address_object]List that contains rendered information about recipients of blind carbon copy.messagestringRendered email template's message.subjectstringRendered email template's subject.


## Email Thread

Example email thread object

```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":false,"root_email_read":false,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z","labels":[],"annotation_counts":{"annotations":4,"annotations_processed":2,"annotations_purged":0,"annotations_rejected":1,"annotations_unprocessed":1}}
```

{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":false,"root_email_read":false,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z","labels":[],"annotation_counts":{"annotations":4,"annotations_processed":2,"annotations_purged":0,"annotations_rejected":1,"annotations_unprocessed":1}}
An email thread object represents thread of related objects in Rossum's inbox.
AttributeTypeRequiredDescriptionRead-onlyidintegerId of the email thread.trueurlURLURL of the email thread.organizationURLURL of the associated organization.truequeueURLURL of the associated queue.trueroot_emailURLURL of the associated root email (first incoming email in the thread).truehas_repliesbooleanTrue if the thread has more than one incoming emails.truehas_new_repliesbooleanTrue if the thread has unread incoming emails.root_email_readbooleanTrue if the root email has been opened in Rossum UI at least once.truecreated_atdatetimeTimestamp of the creation of email thread (inherited from arrived_at timestamp of the root email).truelast_email_created_atdatetimeTimestamp of the most recent email in this email thread.truesubjectstringSubject of the root email.truefromobjectInformation about sender of the root email containing keysemailandname.truelabelslist[string]This attribute is intended forINTERNALuse only and may be changed without notice. List of email thread labels set by root email. If root email is rejected and no other incoming emails are in thread, labels field is set to[rejected]. Labels is an empty list in all the other cases.trueannotation_countsobjectThis attribute is intended forINTERNALuse only and may be changed without notice. Information about how many annotations were extracted from all emails in the thread and in which state they currently aretrue
email
name
[rejected]

#### Thread Annotation counts object

This object stores numbers of annotations extracted from all emails in given email thread.
AttributeTypeDescriptionAnnotation statusannotationsintegerTotal number of annotationsAnyannotations_processedintegerNumber of processed annotationsexported,deleted,purged,splitannotations_purgedintegerNumber of purged annotationspurgedannotations_unprocessedintegerNumber of not yet processed annotationsimporting,failed_import,to_review,reviewing,confirmed,exporting,postponed,failed_exportannotations_rejectedintegerNumber of rejected annotationsrejectedrelated_annotationsintegerTotal number of related annotationsAny
exported
deleted
purged
split
purged
importing
failed_import
to_review
reviewing
confirmed
exporting
postponed
failed_export
rejected

### List all email threads

List all email threads

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_threads'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_threads'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":false,"root_email_read":false,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...},...]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":false,"root_email_read":false,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...},...]}
GET /v1/email_threads
GET /v1/email_threads
Retrieve all email thread objects.

#### Supported filters

Email threads support following filters:
Filter nameTypeDescriptionhas_root_emailbooleanFilter only email threads with a root email.has_repliesbooleanFilter only email threads with two and more emails with typeincomingqueueintegerFilter only email threads associated with given queue id (or multiple ids).has_new_repliesbooleanFilter only email threads with unread emails with typeincomingcreated_at_beforedatetimeFilter only email threads with root email created before given timestamp.created_at_afterdatetimeFilter only email threads with root email created after given timestamp.last_email_created_at_beforedatetimeFilter only email threads with the last email in the thread created before given timestamp.last_email_created_at_afterdatetimeFilter only email threads with the last email in the thread created after given timestamp.recent_with_no_documents_not_repliedbooleanFilter only email threads with root email that arrived in the last 14 days with no attachment processed by Rossum, excluding those: withrejectedlabel, without any reply and when root email has been read.
incoming
incoming
rejected

#### Supported ordering

Email threads support following ordering:id,created_at,last_email_created_at,subject,from__email,from__name,queue
id
created_at
last_email_created_at
subject
from__email
from__name
queue
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofemail threadobjects.

### Retrieve an email thread

Get email thread object1244
1244

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_threads/1244'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_threads/1244'

```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":false,"root_email_read":false,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...}
```

{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":false,"root_email_read":false,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...}
GET /v1/email_threads/{id}
GET /v1/email_threads/{id}
Get an email thread object.

#### Response

Status:200
200
Returnsemail threadobject.

### Update an email thread

Update email thread object1244
1244

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"root_email": "https://<example>.rossum.app/api/v1/emails/5432", "has_new_replies": "True"}'\'https://<example>.rossum.app/api/v1/email_threads/1244'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"root_email": "https://<example>.rossum.app/api/v1/emails/5432", "has_new_replies": "True"}'\'https://<example>.rossum.app/api/v1/email_threads/1244'

```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":true,"root_email_read":true,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...}
```

{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":true,"root_email_read":true,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...}
PUT /v1/email_threads/{id}
PUT /v1/email_threads/{id}
Update email thread object.

#### Response

Status:200
200
Returns updatedemail threadobject.

### Update part of an email thread

Update flag has_new_responses of email thread object1244
1244

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"has_new_replies": "True"}'\'https://<example>.rossum.app/api/v1/emails/1244'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"has_new_replies": "True"}'\'https://<example>.rossum.app/api/v1/emails/1244'

```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":true,"root_email_read":true,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...}
```

{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":true,"root_email_read":true,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...}
PATCH /v1/email_threads/{id}
PATCH /v1/email_threads/{id}
Update part of email thread object.

#### Response

Status:200
200
Returns updatedemail threadobject.

### Get email thread counts

Get email thread counts

```
curl-XGET-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/email_threads/counts'
```

curl-XGET-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/email_threads/counts'

```
{"with_replies":5,"with_new_replies":3,"recent_with_no_documents_not_replied":2}
```

{"with_replies":5,"with_new_replies":3,"recent_with_no_documents_not_replied":2}
GET /v1/email_threads/counts
GET /v1/email_threads/counts
Retrieve counts of email threads.
Supports the same filters aslist email threadsendpoint.

#### Response

Status:200
200
Returns object with email thread counts.
AttributeTypeDescriptionwith_repliesintegerNumber of email threads containing two or moreincomingemailswith_new_repliesintegerNumber of emails threads containing unreadincomingreplies.recent_with_no_documents_not_repliedintegerNumber of email threads with root email that arrived in the last 14 days without any attachments processed by Rossum, excluding those: withrejectedlabel, without any reply (email thread contains only this email) and when root email has been read.
incoming
incoming
rejected


## Generic Engine

Example generic engine object

```
{"id":3000,"url":"https://<example>.rossum.app/api/v1/generic_engines/3000","name":"Generic engine","description":"AI engine trained to recognize data for the specific data capture requirement","documentation_url":"https://rossum.ai/help/faq/generic-ai-engine/","schema":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000"}
```

{"id":3000,"url":"https://<example>.rossum.app/api/v1/generic_engines/3000","name":"Generic engine","description":"AI engine trained to recognize data for the specific data capture requirement","documentation_url":"https://rossum.ai/help/faq/generic-ai-engine/","schema":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000"}
A Generic Engine object holds specification of training setup for Rossum trained Engine.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the generic enginetrueurlURLURL of the generic enginetruenamestringName of the generic enginedescriptionstringDescription of the generic enginedocumentation_urlurlnullURL of the generic engine's documentationschemaurlnullRelatedgeneric engine schema

### List all generic engines

List all generic engines

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engines'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engines'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":3000,"url":"https://<example>.rossum.app/api/v1/generic_engines/3000","name":"Generic engine","description":"AI engine trained to recognize data for the specific data capture requirement","documentation_url":"https://rossum.ai/help/faq/generic-ai-engine/","schema":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000"}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":3000,"url":"https://<example>.rossum.app/api/v1/generic_engines/3000","name":"Generic engine","description":"AI engine trained to recognize data for the specific data capture requirement","documentation_url":"https://rossum.ai/help/faq/generic-ai-engine/","schema":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000"}]}
GET /v1/generic_engines
GET /v1/generic_engines
Retrieve all generic engine objects.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofgeneric engineobjects.

### Retrieve a generic engine

Get generic engine object3000
3000

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engines/3000'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engines/3000'

```
{"id":3000,"url":"https://<example>.rossum.app/api/v1/generic_engines/3000","name":"Generic engine","description":"AI engine trained to recognize data for the specific data capture requirement","documentation_url":"https://rossum.ai/help/faq/generic-ai-engine/","schema":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000"}
```

{"id":3000,"url":"https://<example>.rossum.app/api/v1/generic_engines/3000","name":"Generic engine","description":"AI engine trained to recognize data for the specific data capture requirement","documentation_url":"https://rossum.ai/help/faq/generic-ai-engine/","schema":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000"}
GET /v1/generic_engines/{id}
GET /v1/generic_engines/{id}
Get a generic engine object.

#### Response

Status:200
200
Returnsgeneric engineobject.


## Generic Engine Schema

Example generic engine schema object

```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000","content":{"training_queues":[],"fields":[{"category":"datapoint","engine_output_id":"document_id","type":"string","label":"label text","description":"description text","trained":true,"sources":[]},{"category":"multivalue","engine_output_id":"my_cool_ids","label":"label text","description":"description text","type":"freeform","trained":false,"children":{"category":"datapoint","engine_output_id":"my_cool_id","type":"enum","label":"label text","description":"description text","trained":false,"sources":[]}},{"category":"multivalue","engine_output_id":"date_timezone_table","label":"label text","description":"description text","type":"grid","trained":true,"children":{"category":"tuple","children":[{"category":"datapoint","engine_output_id":"date","type":"date","label":"label text","description":"description text","trained":true,"sources":[]},{"category":"datapoint","engine_output_id":"timezone","type":"string","label":"label text","description":"description text","trained":true,"sources":[]}]}}]}}
```

{"id":6000,"url":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000","content":{"training_queues":[],"fields":[{"category":"datapoint","engine_output_id":"document_id","type":"string","label":"label text","description":"description text","trained":true,"sources":[]},{"category":"multivalue","engine_output_id":"my_cool_ids","label":"label text","description":"description text","type":"freeform","trained":false,"children":{"category":"datapoint","engine_output_id":"my_cool_id","type":"enum","label":"label text","description":"description text","trained":false,"sources":[]}},{"category":"multivalue","engine_output_id":"date_timezone_table","label":"label text","description":"description text","type":"grid","trained":true,"children":{"category":"tuple","children":[{"category":"datapoint","engine_output_id":"date","type":"date","label":"label text","description":"description text","trained":true,"sources":[]},{"category":"datapoint","engine_output_id":"timezone","type":"string","label":"label text","description":"description text","trained":true,"sources":[]}]}}]}}
An engine schema is an object which describes what fields are available in the engine. Do not confuse engine schema withDocument Schema.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the generic engine schematrueurlURLURL of the generic engine schematruecontentobjectSee Dedicated Engine Schema's description of thecontent structure

### List all generic engine schemas

List all generic engine schemas

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engine_schemas'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engine_schemas'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":6000,"url":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":6000,"url":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}]}
GET /v1/generic_engine_schemas
GET /v1/generic_engine_schemas
Retrieve all generic engine schema objects.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofgeneric engine schemaobjects.

### Retrieve a generic engine schema

Get generic engine schema object6000
6000

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engine_schemas/6000'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engine_schemas/6000'

```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
```

{"id":6000,"url":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
GET /v1/generic_engine_schemas/{id}
GET /v1/generic_engine_schemas/{id}
Get a generic engine schema object.

#### Response

Status:200
200
Returnsgeneric engine schemaobject.


## Hook

Example hook object of type webhook

```
{"id":1500,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Change of Status","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"sideload":["queues"],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.east-west-trading.com/api/hook1?strict=true","secret":"secret-token","insecure_ssl":false,"client_ssl_certificate":"-----BEGIN CERTIFICATE-----\n...","timeout_s":30,"retry_count":4,"app":{"display_mode":"drawer","url":"https://myq.east-west-trading.com/api/hook1?strict=true","settings":{},}},"test":{"saved_input":{...}},"extension_source":"custom","settings":{},"settings_schema":{"type":"object","properties":{}},"secrets":{},"secrets_schema":{"type":"object","properties":{}},"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":"https://<example>.rossum.app/api/v1/hook_templates/998877","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":1500,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Change of Status","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"sideload":["queues"],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.east-west-trading.com/api/hook1?strict=true","secret":"secret-token","insecure_ssl":false,"client_ssl_certificate":"-----BEGIN CERTIFICATE-----\n...","timeout_s":30,"retry_count":4,"app":{"display_mode":"drawer","url":"https://myq.east-west-trading.com/api/hook1?strict=true","settings":{},}},"test":{"saved_input":{...}},"extension_source":"custom","settings":{},"settings_schema":{"type":"object","properties":{}},"secrets":{},"secrets_schema":{"type":"object","properties":{}},"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":"https://<example>.rossum.app/api/v1/hook_templates/998877","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
Example hook object of type function

```
{"id":1500,"type":"function","url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Empty function","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"sideload":["modifiers"],"active":true,"events":["annotation_status.changed"],"config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};","timeout_s":30,"retry_count":4,"app":{"display_mode":"drawer","url":"https://myq.east-west-trading.com/api/hook1?strict=true","settings":{},}},"token_owner":"https://<example>.rossum.app/api/v1/users/12345","token_lifetime_s":1000,"test":{"saved_input":{...}},"status":"ready","extension_source":"custom","settings":{},"settings_schema":{"type":"object","properties":{}},"secrets":{},"secrets_schema":{"type":"object","properties":{}},"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":"https://<example>.rossum.app/api/v1/hook_templates/998877","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":1500,"type":"function","url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Empty function","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"sideload":["modifiers"],"active":true,"events":["annotation_status.changed"],"config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};","timeout_s":30,"retry_count":4,"app":{"display_mode":"drawer","url":"https://myq.east-west-trading.com/api/hook1?strict=true","settings":{},}},"token_owner":"https://<example>.rossum.app/api/v1/users/12345","token_lifetime_s":1000,"test":{"saved_input":{...}},"status":"ready","extension_source":"custom","settings":{},"settings_schema":{"type":"object","properties":{}},"secrets":{},"secrets_schema":{"type":"object","properties":{}},"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":"https://<example>.rossum.app/api/v1/hook_templates/998877","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
A hook is an extension of Rossum that is notified when specific event occurs.
A hook object is used to configure what endpoint or function is executed and
when. For an overview of other extension options seeExtensions.
run_after
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the hooktruetypestringwebhookHook type. Possible values:webhook,functionnamestringName of the hookurlURLURL of the hooktruequeueslist[URL]List of queues that use hook object.run_afterlist[URL]List of all hooks that has to be executed before running this hook.activeboolIf set totruethe hook is notified.eventslist[string]List of events, when the hook should be notified. For the list of events seeWebhook events.sideloadlist[string][]List of related objects that should be included in hook request. For the list of possible sideloads seeWebhook events.metadataobject{}Client data.configobjectConfiguration of the hook.token_ownerURLURL of a user object. If present, an API access token is generated for this user andsent to the hook. Users with organization group admin cannot be set as token_owner. Ifnull, token is not generated.token_lifetime_sintegernullLifetime number of seconds forrossum_authorization_token(min=0, max=7200). This setting will ensure the token will be valid after hook response is returned. Ifnull, default lifetime of600is used.testobject{}Input saved for hook testing purposes, seeTest a hookdescriptionstringHook description text.extension_sourcestringcustomImport source of the extension.settingsobject{}Specific settings that will be included in the payload when executing the hook. Field is validated with json schema stored insettings_schemafield.settings_schemaobjectnull[BETA]JSON schema forsettingsfield validation.secretsobject{}Specific secrets that are stored securely encrypted. The values are merged into the hook execution payload. Field is validated with json schema stored insecrets_schemafield.  (write only)secrets_schemaobjectJSON schema[BETA]JSON schema forsecretsfield validation.guidestringDescription how to use the extension.read_more_urlURLURL address leading to more info page.extension_image_urlURLURL address of extension picture.hook_templateURLnullURL of the hook template used to create the hookcreated_byURLnullURL of the hook creator. Might benullfor hooks created before April 2025.truecreated_atdatetimenullDate of hook creation. Might benullfor hooks created before April 2025.truemodified_byURLnullURL of the last hook modifiertruemodified_atdatetimenullDate of last modificationtrue
webhook
function
true
[]
{}
null
null
rossum_authorization_token
null
600
{}
{}
settings_schema
null
settings
{}
secrets_schema
secrets
null
null
null
null
null
null
null

#### Config attribute

Config attribute allows to specify per-type configuration.
AttributeTypeDefaultDescriptionurlURLURL of the webhook endpoint to callsecretstring(optional) If set, it is used to create a hash signature with each payload. For more information seeValidating payloads from Rossuminsecure_sslboolfalseDisable SSL certificate verification (only use for testing purposes).client_ssl_certificatestringClient SSL certificate used to authenticate requests. Must be PEM encoded.client_ssl_keystringClient SSL key (write only). Must be PEM encoded. Key may not be encrypted.privateboolfalse(optional) If set, theurlandsecretvalues become hidden and immutable once the hook is created. The value of this flag cannot be changed tofalseonce set.scheduleobject{}Specific configuration for hooks of invocation.scheduled event and action interval. Seescheduletimeout_sint30Webhook call timeout in seconds. For non-interactive webhooks only (min=0, max=60).retry_countint4Number of times the webhook call is retried in case of failure. For non-interactive webhooks only (min=0, max=4).max_polling_time_sint300The maximum polling time in seconds forasynchronous webhooks(min=1, max=3600). It is possible to configure this value only forupload.createdandinvocation.scheduledevents. For other non-interactive events the default value is used.retry_after_polling_failurebooltrueIf set totrue, the original webhook call is retried in case the polling fails. See theasynchronous webhookssection for more details. Possible to configure only forupload.createdandinvocation.scheduledevents. For other non-interactive events the default value is used.appobj(deprecated) (optional) Configuration of the apppayload_logging_enabledboolfalse(optional) If set to False, hook payload is omited from hook logs feature accessible via UIretry_on_any_non_2xxboolfalse(optional) Disabling this option results in retrying only on these response statuses: [408, 429, 500, 502, 503, 504]
false
false
url
secret
false
{}
30
4
300
upload.created
invocation.scheduled
true
true
upload.created
invocation.scheduled
false
false
AttributeTypeDefaultDescriptionruntimestringRuntime used to execute code. Allowed values:nodejs22.xorpython3.12.codestringString-serialized source code to be executedthird_party_library_packstringdefaultSet of libraries to be included in execution environment of the function, seedocumentation belowfor details.privateboolfalse(optional) If set, theruntime,codeandthird_party_library_packvalues become hidden and immutable once the hook is created. The value of this flag cannot be changed tofalseonce set.scheduleobj{}Specific configuration for hooks of invocation.scheduled event and action interval. Seescheduletimeout_sint30Function call timeout in seconds. For non-interactive functions only (min=0, max=60)memory_size_mbint256Function memory limit (min=128, max=256). The limit can be increased upon request.retry_countint4Number of times the function call is retried in case of failure. For non-interactive functions only (min=0, max=4).appobj(deprecated) (optional) Configuration of the apppayload_logging_enabledboolfalse(optional) If set to False, hook payload is omited from hook logs feature accessible via UI
nodejs22.x
python3.12
default
false
runtime
code
third_party_library_pack
false
{}
30
256
4
false

#### Schedule object

Scheduleobject contains the following additional event-specific attributes.Cronobject interval can't be shorter than every 10 minutes.
Schedule
Cron
KeyTypeDescriptioncronobjectUsed to set interval withcron expressionin UTC timezone.

#### App object (deprecated)

TheAppobject contains the following attributes.
App
KeyTypeDefaultDescriptionRequiredurlURLURL of the app that will be embedded in Rossum UI.TruesettingsobjectSettings of the app that can be used for further customization of configuration app (such as UI schema etc.)Falsedisplay_modestringdrawerDisplay mode of the app
drawer
Currently, there are two display modes supported.
display_modeDescriptiondraweropens a drawer with embedded URLfullscreenopens an embedded URL in full-screen overlay
drawer
fullscreen
Libraries available in the execution environment can be configured via optionthird_party_library_pack.
Please note that functions with third party libraries need up to 30 seconds to update the code.
third_party_library_pack
Let us knowif you need any additional libraries.
ValueTypeDescriptionnullobjectOnly standard Python Standard Library is availabledefaultstringContains additional librariesrossum,requests,jmespath,xmltodict,pydantic,pandas,httpx,boto3andbotocore
rossum
requests
jmespath
xmltodict
pydantic
pandas
httpx
boto3
botocore
ValueTypeDescriptionnullobjectOnly Node.js Built-in Modules are availabledefaultstringContains additional librariesnode-fetch,https-proxy-agentandlodash
node-fetch
https-proxy-agent
lodash
AttributeTypeDescriptionRead-onlystatusstringStatus indicates whether the function is ready to be invoked or modified. Possible values areready,pendingorfailed. While the state ispending, invocations and other API actions that operate on the function return status 400. It is recommended to resave function forfailedstate.True
ready
pending
failed
pending
failed
This value indicates where the hook has been imported from.
ValueDescriptioncustomThe Hook has been imported and set up by the user.rossum_storeA preconfigured Hook has been imported from an extension store.
The content ofsecretsis stored encrypted and is write-only in the API. There is an additionalsecrets_schemaproperty to provide a JSON schema forsecretsvalidation.
secrets
secrets_schema
secrets
To getsecretsas a list of keys, please refer toRetrieve list of secrets keys
secrets
JSON schema for the hooksecretsproperties. Schema needs to includeadditionalProperties. This needs to be either set tofalse(as shown in the example), so no additional properties than the ones specified in this schema are allowed forsecretsfield, or set to an object with"type": "string"property (as shown in the default value), to ensure all additional properties are of type string. More onadditionalPropertiescan be found in the officialdocs
secrets
additionalProperties
false
secrets
"type": "string"
additionalProperties
Example of Secrets schema object for validating two secrets properties

```
{"type":"object","properties":{"username":{"type":"string","description":"Target system user",},"password":{"type":"string","description":"Target system user password",}},"additionalProperties":false}
```

{"type":"object","properties":{"username":{"type":"string","description":"Target system user",},"password":{"type":"string","description":"Target system user password",}},"additionalProperties":false}
Default value of secrets_schema field

```
{"type":"object","additionalProperties":{"type":"string"}}
```

{"type":"object","additionalProperties":{"type":"string"}}
JSON schema for the hooksettingsvalidation.
settings
Example of Settings schema object for validating two settings properties

```
{"type":"object","properties":{"username":{"type":"string","description":"Target system user",},"password":{"type":"string","description":"Target system user password",}}}
```

{"type":"object","properties":{"username":{"type":"string","description":"Target system user",},"password":{"type":"string","description":"Target system user password",}}}

### List all hooks

List all hooks

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Some Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.east-west-trading.com/api/hook1?strict=true","schedule":{"cron":"*/10 * * * *"}},"test":{"saved_input":{...}},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Some Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.east-west-trading.com/api/hook1?strict=true","schedule":{"cron":"*/10 * * * *"}},"test":{"saved_input":{...}},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
GET /v1/hooks
GET /v1/hooks
Retrieve all hook objects.
Supported filters:id,name,type,queue,active,config_url,config_app_url,extension_source,events
id
name
type
queue
active
config_url
config_app_url
extension_source
events
Supported ordering:id,name,type,active,config_url,config_app_url,events
id
name
type
active
config_url
config_app_url
events
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofhookobjects.

### List Hook Call Logs

Get a list of hook call logs

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/hooks/logs'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/hooks/logs'

```
{"results":[{"timestamp":"2023-09-23T12:00:00.000000Z","request_id":"6166deb3-2f89-4fc2-9359-56cc8e3838e4","event":"annotation_content","action":"updated","annotation_id":1,"queue_id":1,"hook_id":1,"hook_type":"webhook","log_level":"INFO","message":"message","request":"{}","response":"{}","start":"2023-09-23T12:00:00.000000Z","end":"2023-09-23T12:00:00.000000Z","settings":"{}","status":"completed","uuid":"6166deb3-2f89-4fc2-9359-56cc8e3838e4"},{"timestamp":"2023-09-23T12:00:00.000000Z","request_id":"1234abc1-1bg3-4cf2-9876-32aa8e3434a2","event":"email","action":"received","email_id":1,"queue_id":1,"hook_id":1,"hook_type":"webhook","log_level":"INFO","message":"message","request":"{}","response":"{}","start":"2023-09-23T12:00:00.000000Z","end":"2023-09-23T12:00:00.000000Z","settings":"{}","status":"completed","uuid":"1234abc1-1bg3-4cf2-9876-32aa8e3434a2"}]}
```

{"results":[{"timestamp":"2023-09-23T12:00:00.000000Z","request_id":"6166deb3-2f89-4fc2-9359-56cc8e3838e4","event":"annotation_content","action":"updated","annotation_id":1,"queue_id":1,"hook_id":1,"hook_type":"webhook","log_level":"INFO","message":"message","request":"{}","response":"{}","start":"2023-09-23T12:00:00.000000Z","end":"2023-09-23T12:00:00.000000Z","settings":"{}","status":"completed","uuid":"6166deb3-2f89-4fc2-9359-56cc8e3838e4"},{"timestamp":"2023-09-23T12:00:00.000000Z","request_id":"1234abc1-1bg3-4cf2-9876-32aa8e3434a2","event":"email","action":"received","email_id":1,"queue_id":1,"hook_id":1,"hook_type":"webhook","log_level":"INFO","message":"message","request":"{}","response":"{}","start":"2023-09-23T12:00:00.000000Z","end":"2023-09-23T12:00:00.000000Z","settings":"{}","status":"completed","uuid":"1234abc1-1bg3-4cf2-9876-32aa8e3434a2"}]}
GET /v1/hooks/logs
GET /v1/hooks/logs
List all the logs from all running hooks. The logs are sorted by thestarttimestamp in descending order.
start
Supported filters:
Filter nameTypeDescriptionrequest_idstringMatch the specifiedrequest_id.log_levelstringMatch the specified log level (or multiple log levels).hookintegerMatch given the hook id (or multiple ids).timestamp_beforedatetimeFilter for log entries before given timestamp.timestamp_afterdatetimeFilter for log entries after given timestamp.start_beforedatetimeFilter for log entries before given start timestamp.start_afterdatetimeFilter for log entries after given start timestamp.statusstringMatch the log entrystatus(or multiple statuses). Available choices:waiting,running,completed,cancelled,failed.status_codeintegerMatch the responsestatus_code(or multiple).queueintegerMatch the given queue id (or multiple ids).annotationintegerMatch the given annotation id (or multiple ids).emailintegerMatch the given email id (or multiple ids).searchstringFull text filter across all the log entry fields.page_sizeintegerMaximum number of results to return (between 1 and 100, defaults to 100).
request_id
status
waiting
running
completed
cancelled
failed
status_code
The retention policy for the logs is set to 7 days.
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returns list of thehook logs

### Create a new hook

Create new hook related to queue8199with endpoint URLhttps://myq.east-west-trading.com
8199
https://myq.east-west-trading.com

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Hook", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "config": {"url": "https://myq.east-west-trading.com"}, "events": []}'\'https://<example>.rossum.app/api/v1/hooks'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Hook", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "config": {"url": "https://myq.east-west-trading.com"}, "events": []}'\'https://<example>.rossum.app/api/v1/hooks'

```
{"id":1501,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1501","name":"MyQ Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199"],"run_after":[],"active":true,"events":[],"config":{"url":"https://myq.east-west-trading.com","schedule":{}},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":null,"read_more_url":null,"extension_image_url":null}
```

{"id":1501,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1501","name":"MyQ Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199"],"run_after":[],"active":true,"events":[],"config":{"url":"https://myq.east-west-trading.com","schedule":{}},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":null,"read_more_url":null,"extension_image_url":null}
POST /v1/hooks
POST /v1/hooks
Create a new hook object.

#### Response

Status:201
201
Returns createdhookobject.

### Create a new hook from hook template

Create new hook using a hook template referencehttps://<example>.rossum.app/api/v1/hook_templates/5
https://<example>.rossum.app/api/v1/hook_templates/5

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyT Hook", "hook_template": "https://<example>.rossum.app/api/v1/hook_templates/5", "events": ["annotation_status.changed"]}',"queues":[]\'https://<example>.rossum.app/api/v1/hooks/create'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyT Hook", "hook_template": "https://<example>.rossum.app/api/v1/hook_templates/5", "events": ["annotation_status.changed"]}',"queues":[]\'https://<example>.rossum.app/api/v1/hooks/create'

```
{"id":1502,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1502","name":"MyT Hook","metadata":{},"queues":[],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"private":true},"test":{},"settings":{},"settings_schema":null,"description":"A closed source hook created from an extension store hook template...","extension_source":"rossum_store","guide":null,"read_more_url":null,"extension_image_url":null,"hook_template":"https://<example>.rossum.app/api/v1/hook_templates/5","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":1502,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1502","name":"MyT Hook","metadata":{},"queues":[],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"private":true},"test":{},"settings":{},"settings_schema":null,"description":"A closed source hook created from an extension store hook template...","extension_source":"rossum_store","guide":null,"read_more_url":null,"extension_image_url":null,"hook_template":"https://<example>.rossum.app/api/v1/hook_templates/5","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
POST /v1/hooks/create
POST /v1/hooks/create
Create a new hook object with the option to use a referenced hook template as a base.

#### Response

Status:201
201
Returns createdhookobject.

### Retrieve a hook

Get hook object1500
1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500'

```
{"id":1500,"url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Some Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.east-west-trading.com/api/hook1?strict=true"},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":null,"created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":1500,"url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Some Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.east-west-trading.com/api/hook1?strict=true"},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":null,"created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
GET /v1/hooks/{id}
GET /v1/hooks/{id}
Get an hook object.

#### Response

Status:200
200
Returnshookobject.

### Update a hook

Update hook object1500
1500

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Hook (stg)", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "config": {"url": "https://myq.stg.east-west-trading.com"}, "events": []} \
  'https://<example>.rossum.app/api/v1/hooks/1500'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Hook (stg)", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "config": {"url": "https://myq.stg.east-west-trading.com"}, "events": []} \
  'https://<example>.rossum.app/api/v1/hooks/1500'

```
{"id":1500,"url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"MyQ Hook (stg)","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199"],"run_after":[],"active":true,"events":[],"config":{"url":"https://myq.stg.east-west-trading.com"},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":null,"read_more_url":null,"extension_image_url":null,"hook_template":null,"created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":1500,"url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"MyQ Hook (stg)","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199"],"run_after":[],"active":true,"events":[],"config":{"url":"https://myq.stg.east-west-trading.com"},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":null,"read_more_url":null,"extension_image_url":null,"hook_template":null,"created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
PUT /v1/hooks/{id}
PUT /v1/hooks/{id}
Update hook object.

#### Response

Status:200
200
Returns updatedhookobject.

### Update part of a hook

Update hook URL of hook object1500
1500

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"config": {"url": "https://myq.stg2.east-west-trading.com"}}'\'https://<example>.rossum.app/api/v1/hooks/1500'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"config": {"url": "https://myq.stg2.east-west-trading.com"}}'\'https://<example>.rossum.app/api/v1/hooks/1500'

```
{"id":1500,"url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Some Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.stg2.east-west-trading.com"},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":null,"created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":1500,"url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Some Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.stg2.east-west-trading.com"},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":null,"created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
PATCH /v1/hooks/{id}
PATCH /v1/hooks/{id}
Update part of hook object.

#### Response

Status:200
200
Returns updatedhookobject.

### Delete a hook

Delete hook1500
1500

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500'
DELETE /v1/hooks/{id}
DELETE /v1/hooks/{id}
Delete hook object.

#### Response

Status:204
204

### Duplicate a hook

Duplicate existing hook object123
123

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Duplicate Hook", "copy_secrets": true, "copy_dependencies": true}'\'https://<example>.rossum.app/api/v1/hooks/123/duplicate'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Duplicate Hook", "copy_secrets": true, "copy_dependencies": true}'\'https://<example>.rossum.app/api/v1/hooks/123/duplicate'

```
{"id":124,"name":"Duplicate Hook","url":"https://<example>.rossum.app/api/v1/hooks/124",...}
```

{"id":124,"name":"Duplicate Hook","url":"https://<example>.rossum.app/api/v1/hooks/124",...}
POST /v1/hooks/{id}/duplicate
POST /v1/hooks/{id}/duplicate
Duplicate a hook object.hook.queuesis not copied. Duplicated hook is always inactive (hook.active = False).
hook.queues
hook.active = False
AttributeTypeDefaultDescriptionnamestringName of the duplicated hook.copy_secretsboolfalseWhether to copy secrets.copy_dependenciesboolfalseWhether to copy dependencies. If enabled, this option copies the dependency relations of the original hook. It duplicates therun_afterreferences to preserve which hooks the original hook depended on, and it also updates all hooks that previously depended on the original hook to reference the new duplicated one. This ensures that both dependency directions—“runs after” and “is run after by”—are correctly maintained.
run_after

#### Response

Status:201
201
Returns duplicate ofhookobject.

### Test a hook

Call webhook1500and display its result
1500

```
curl'https://<example>.rossum.app/api/v1/hooks/1500/test'-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{
  "config": {
    "insecure_ssl": true
  },
  "payload": {
    "action": "started",
    "event": "annotation_content",
    "annotation": {},
    "document": {},
    "settings": {}
  }
}'
```

curl'https://<example>.rossum.app/api/v1/hooks/1500/test'-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{
  "config": {
    "insecure_ssl": true
  },
  "payload": {
    "action": "started",
    "event": "annotation_content",
    "annotation": {},
    "document": {},
    "settings": {}
  }
}'

```
{"response":{"messages":[],"operations":[]}}
```

{"response":{"messages":[],"operations":[]}}
Call serverless function (code may be specified in the request) and display its result

```
curl'https://<example>.rossum.app/api/v1/hooks/1501/test'-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{
  "config": {
    "code": "exports.rossum_hook_request_handler = ..."
  },
  "payload": {
    "action": "started",
    "event": "annotation_content",
    "annotation": {},
    "document": {},
    "settings": {}
  }
}'
```

curl'https://<example>.rossum.app/api/v1/hooks/1501/test'-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{
  "config": {
    "code": "exports.rossum_hook_request_handler = ..."
  },
  "payload": {
    "action": "started",
    "event": "annotation_content",
    "annotation": {},
    "document": {},
    "settings": {}
  }
}'

```
{"response":{"messages":[],"operations":[]}}
```

{"response":{"messages":[],"operations":[]}}
POST /v1/hooks/{id}/test
POST /v1/hooks/{id}/test
Test a hook with custom payload. Test endpoint will return result generated by the specified Hook which would be normally processed by Rossum.
AttributeTypeRequiredDescriptionconfigobjectfalseYou can override defaultconfigurationof hook being executed. Theruntimeattribute is required for function hook if custom config is set.payloadobjecttruePayload sent to the Hook, please note onlysupportedcombination ofactionandeventcan be passed.
runtime
action
event

#### Response

Status:200in case of success.409in case the test function is not ready yet -- then request should be retried after 10 seconds.
200
409

### Manual hook trigger

Example data sent forinvocation.manualevent and action with extra arguments
invocation.manual

```
curl'https://<example>.rossum.app/api/v1/hooks/789/invoke'-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"SAP_ID": "1234", "DB_COLUMN": "SAP"}'
```

curl'https://<example>.rossum.app/api/v1/hooks/789/invoke'-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"SAP_ID": "1234", "DB_COLUMN": "SAP"}'
Example data sent frominvocation.manualhook to your client following the request above
invocation.manual

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/789","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"my-rossum-importer","password":"secret-importer-user-password"},"action":"manual","event":"invocation","SAP_ID":"1234","DB_COLUMN":"SAP"}
```

{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/789","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"my-rossum-importer","password":"secret-importer-user-password"},"action":"manual","event":"invocation","SAP_ID":"1234","DB_COLUMN":"SAP"}
POST /v1/hooks/{id}/invoke
POST /v1/hooks/{id}/invoke
Invoke the hook with custom payload. The payload will be added to the standardinvocationevent hook request and sent to the hook. The hook response is returned in the invocation response payload.
invocation
request_id
action
timeout_s
config
POST /v1/hooks/{id}/invoke

#### Payload

Object with properties to be merged into the invocation payload.

#### Response

Status:200in case of success.400in case of not having proper event and action in hook object or non-json response.
200
400

### Retrieve list of secrets keys

Get secret_keys of hook object1500
1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500/secrets_keys'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500/secrets_keys'

```
["secret_key1","secret_key2"]
```

["secret_key1","secret_key2"]
GET /v1/hooks/{id}/secrets_keys
GET /v1/hooks/{id}/secrets_keys
Retrieve all secrets in a list (only keys are retrieved, values are encrypted in DB and aren't possible to obtain via API)

#### Response

Status:200
200
Returns list ofhook secretskeys.

### Generate payload for hook

Generate hook payload for hook object1500
1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500/generate_payload'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500/generate_payload'

```
{"event":"invocation","action":"scheduled"}
```

{"event":"invocation","action":"scheduled"}
Users can use this endpoint to test the hook on a payload of specific events and actions.
Example data forinvocation.scheduledhook
invocation.scheduled

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/1500","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"[redacted...]","password":"[redacted...]"},"action":"schedule","event":"invocation"}
```

{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/1500","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"[redacted...]","password":"[redacted...]"},"action":"schedule","event":"invocation"}
POST /v1/hooks/{id}/generate_payload
POST /v1/hooks/{id}/generate_payload
AttributeTypeRequiredDescriptionactionstringtrueHook'sactioneventstringtrueHook'seventannotationURLURL of related Annotation object. Required for annotation_status and annotation_content events.previous_statusenumA previous status of the document. SeeDocument Lifecyclefor a list of supported values. Required for annotation_status and annotation_content events.statusenumStatus of the document. SeeDocument Lifecyclefor a list of supported values. Required for annotation_status and annotation_content events.emailURLURL of the arriving email. Required for email event.uploadURLURL of an upload instance. Required for upload event.

#### Response

Status:200
200
Returnshookpayload for specific event and action. The token used for calling the endpoint is returned asrossum_authorization_tokenregardless of thetoken_ownerof the hook.
Values insecretsare redacted as shown in the example for security reasons. The payload for email events from this endpoint may differ from the original hook payload in the file ids,
height, width, and format of email addresses in headers.
rossum_authorization_token
token_owner
secrets


## Hook Template

Example hook template object

```
{"url":"https://<example>.rossum.app/api/v1/hook_templates/1","metadata":{},"events":["annotation_status.changed"],"test":{"hook":"https://<example>.rossum.app/api/v1/hooks/789","event":"annotation_status","action":"changed","document":{...},"settings":{"rules":[{"value":"receipt","schema_id":"document_type","target_queue":128153,"target_status":"to_review","trigger_status":"to_review"},{"value":"invoice","schema_id":"document_type","target_queue":108833,"target_status":"to_review","trigger_status":"to_review"}]},"timestamp":"2020-01-01T00:00:00.000000Z","annotation":{...},"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","base_url":"https://<example>.rossum.app"},"settings":{"rules":[{"value":"receipt","schema_id":"document_type","target_queue":128153,"target_status":"to_review","trigger_status":"to_review"},{"value":"invoice","schema_id":"document_type","target_queue":108833,"target_status":"to_review","trigger_status":"to_review"}]},"settings_description":[{"name":"Rules","description":"List of rules to be applied."},{"name":"Target queue","description":"The ID of the queue where the document will move."}],"name":"Document sorting","type":"function","config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};""schedule":{"cron":"*/10 * * * *"}},"sideload":["queues"],"description":"Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.","extension_source":"rossum_store","settings_schema":null,"secrets_schema":null,"store_description":"<p>Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.</p>","external_url":"","use_token_owner":true,"install_action":"copy","token_lifetime_s":null,"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg"}
```

{"url":"https://<example>.rossum.app/api/v1/hook_templates/1","metadata":{},"events":["annotation_status.changed"],"test":{"hook":"https://<example>.rossum.app/api/v1/hooks/789","event":"annotation_status","action":"changed","document":{...},"settings":{"rules":[{"value":"receipt","schema_id":"document_type","target_queue":128153,"target_status":"to_review","trigger_status":"to_review"},{"value":"invoice","schema_id":"document_type","target_queue":108833,"target_status":"to_review","trigger_status":"to_review"}]},"timestamp":"2020-01-01T00:00:00.000000Z","annotation":{...},"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","base_url":"https://<example>.rossum.app"},"settings":{"rules":[{"value":"receipt","schema_id":"document_type","target_queue":128153,"target_status":"to_review","trigger_status":"to_review"},{"value":"invoice","schema_id":"document_type","target_queue":108833,"target_status":"to_review","trigger_status":"to_review"}]},"settings_description":[{"name":"Rules","description":"List of rules to be applied."},{"name":"Target queue","description":"The ID of the queue where the document will move."}],"name":"Document sorting","type":"function","config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};""schedule":{"cron":"*/10 * * * *"}},"sideload":["queues"],"description":"Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.","extension_source":"rossum_store","settings_schema":null,"secrets_schema":null,"store_description":"<p>Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.</p>","external_url":"","use_token_owner":true,"install_action":"copy","token_lifetime_s":null,"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg"}
Hook template is a definition of hook in Rossum extension store.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the hooktruetypestringwebhookHook type. Possible values:webhook,functionnamestringName of the hookurlURLURL of the hooktrueeventslist[string]List of events, when the hook should be notified. For the list of events seeWebhook events.sideloadlist[string][]List of related objects that should be included in hook request. For the list of possible sideloads seeWebhook events.metadataobject{}Client data.configobjectConfiguration of the hook.testobject{}Input saved for hook testing purposes, seeTest a hookdescriptionstringHook description text.extension_sourcestringrossum_storeImport source of the extension. For more, seeExtension sources.settingsobject{}Specific settings that will be included in the payload when executing the hook.settings_schemaobjectnullJSON schema for settings field, specifying the JSON structure of this field. (seeHook settings schema)secrets_schemaobjectnullJSON schema for secrets field, specifying the JSON structure of this field. (seeHook secrets schema)guidestringDescription how to use the extension.read_more_urlURLURL address leading to more info page.extension_image_urlURLURL address of extension picture.settings_descriptionlist[object][]Contains description for settingsstore_descriptionstringDescription of hook displayed in Rossum store.external_urlstringExternal URL to be called (relates towebhooktype).use_token_ownerbooleanfalseWhether the hook should use token owner.install_actionstringcopyWhether the hook is added directly via application (copy) or on customer's request (request_access).token_lifetime_sintegernullLifetime number of seconds forrossum_authorization_token(min=0, max=7200). This setting will ensure the token will be valid after hook response is returned. Ifnull, default lifetime of600is used.orderinteger0Hook templates can be ordered or grouped by this parameter.
webhook
function
[]
{}
{}
{}
null
null
[]
webhook
copy
request_access
null
rossum_authorization_token
null
600

#### Settings description object

AttributeTypeDefaultDescriptionnamestringName of settings attributedescriptionstringDescription of settings attributetooltipstringTooltip for the attribute

#### Hook template variables

You can use variable substitution in Hook Templates. To use it, surround an available variable like
so{{magic_variable}}anywhere in the request body. If the variable is available, it will be replaced.
If the variable is not available, response will return500.
{{magic_variable}}
500
Variableapi_urlwebhook_base_domainwebhook_domain_prefix

### List all hook templates

List all hook templates

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hook_templates'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hook_templates'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/hook_templates/1","metadata":{},"events":["annotation_status.changed"],"test":{...},"settings":{...},"settings_description":[...],"settings_schema":null,"secrets_schema":null,"name":"Document sorting","type":"function","config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};"},"sideload":["queues"],"description":"Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.","extension_source":"rossum_store","store_description":"<p>Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.</p>","external_url":"","use_token_owner":true,"install_action":"copy","token_lifetime_s":null,"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg"}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/hook_templates/1","metadata":{},"events":["annotation_status.changed"],"test":{...},"settings":{...},"settings_description":[...],"settings_schema":null,"secrets_schema":null,"name":"Document sorting","type":"function","config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};"},"sideload":["queues"],"description":"Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.","extension_source":"rossum_store","store_description":"<p>Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.</p>","external_url":"","use_token_owner":true,"install_action":"copy","token_lifetime_s":null,"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg"}]}
GET /v1/hook_templates
GET /v1/hook_templates
Retrieve all hook template objects.
Supported ordering:order
order

#### Response

Status:200
200
Returnspaginatedresponse with a list ofhook templatesobjects.

### Retrieve a hook template

Get hook template object1
1

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hook_templates/1'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hook_templates/1'

```
{"url":"https://<example>.rossum.app/api/v1/hook_templates/1","metadata":{},"events":["annotation_status.changed"],"test":{...},"settings":{...},"settings_description":[...],"settings_schema":null,"secrets_schema":null,"name":"Document sorting","type":"function","config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};"},"sideload":["queues"],"description":"Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.","extension_source":"rossum_store","store_description":"<p>Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.</p>","external_url":"","use_token_owner":true,"install_action":"copy","token_lifetime_s":null,"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg"}
```

{"url":"https://<example>.rossum.app/api/v1/hook_templates/1","metadata":{},"events":["annotation_status.changed"],"test":{...},"settings":{...},"settings_description":[...],"settings_schema":null,"secrets_schema":null,"name":"Document sorting","type":"function","config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};"},"sideload":["queues"],"description":"Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.","extension_source":"rossum_store","store_description":"<p>Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.</p>","external_url":"","use_token_owner":true,"install_action":"copy","token_lifetime_s":null,"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg"}
GET /v1/hook_templates/{id}
GET /v1/hook_templates/{id}
Get a hook template object.

#### Response

Status:200
200
Returnshook templateobject.


## Inbox

Example inbox object

```
{"id":1234,"name":"Receipts","url":"https://<example>.rossum.app/api/v1/inboxes/1234","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"email":"east-west-trading-co-a34f3a@<example>.rossum.app","email_prefix":"east-west-trading-co","bounce_email_to":"bounces@east-west.com","bounce_unprocessable_attachments":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":true,"metadata":{},"filters":{"allowed_senders":["*@rossum.ai","john.doe@company.com","john.doe@company.??"],"denied_senders":["spam@*"],"document_rejection_conditions":{"enabled":true,"resolution_lower_than_px":[1200,600],"file_size_less_than_b":null,"mime_types":["image/gif"],"file_name_regexes":null}},"dmarc_check_action":"accept","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z"}
```

{"id":1234,"name":"Receipts","url":"https://<example>.rossum.app/api/v1/inboxes/1234","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"email":"east-west-trading-co-a34f3a@<example>.rossum.app","email_prefix":"east-west-trading-co","bounce_email_to":"bounces@east-west.com","bounce_unprocessable_attachments":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":true,"metadata":{},"filters":{"allowed_senders":["*@rossum.ai","john.doe@company.com","john.doe@company.??"],"denied_senders":["spam@*"],"document_rejection_conditions":{"enabled":true,"resolution_lower_than_px":[1200,600],"file_size_less_than_b":null,"mime_types":["image/gif"],"file_name_regexes":null}},"dmarc_check_action":"accept","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z"}
An inbox object enables email ingestion to a relatedqueue. We
enforceemaildomain to match Rossum domain (e.g..rossum.app).email_prefixmay be used to construct unique email address.
email
email_prefix
Please note that due to security reasons, emails from Rossum do not contain processed files.
This feature can be enabled upon request by customer support.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the inboxtruenamestringName of the inbox (not visible in UI)urlURLURL of the inboxtruequeueslist[URL]Queue that receives documents from inbox. Queue has to be passed in list due to backward compatibility. It is possible to have only one queue per inbox.emailEMAILRossum email address (e.g.east-west-trading-co-a34f3a@<example>.rossum.app)email_prefixstringRossum email address prefix (e.g.east-west-trading-co). Maximum length allowed is 57 chars.bounce_email_toEMAIL(Deprecated) Email address to send notifications to (e.g. about failed import). Configuration moved toEmail notifications settings.bounce_unprocessable_attachmentsboolfalse(Deprecated) Whether return back unprocessable attachments (e.g. MS Word docx) or just silently ignore them. When true,minimum image sizerequirement does not apply. Configuration moved toEmail notifications settings.bounce_postponed_annotationsboolfalse(Deprecated) Whether to send notification when annotation is postponed. Configuration moved toEmail notifications settings.bounce_deleted_annotationsboolfalse(Deprecated) Whether to send notification when annotation is deleted. Configuration moved toEmail notifications settings.bounce_email_with_no_attachmentsbooltrue(Deprecated) Whether to send notification when no processable documents were found. Configuration moved toEmail notifications settings.metadataobject{}Client data.filtersobject{}Filtering of incoming emails and documents, seefiltersdmarc_check_actionstringacceptDecides what to do with incoming emails, that don't pass the DMARC check. Available values areacceptanddrop.modified_byURLnullLast modifier.truemodified_atdatetimenullTime of last modification.true
east-west-trading-co-a34f3a@<example>.rossum.app
east-west-trading-co
false
false
false
true
{}
{}
accept
accept
drop
null
null

#### Filters attribute

allowed_sendersanddenied_senderssettings allow filtering of incoming emails based on sender email address. Filters can be specified by exact
email addresses as well as using expressions containing wildcards:
allowed_senders
denied_senders
- *matches everything (e.g.*@rossum.aimatches every email fromrossum.aidomain)
*
*@rossum.ai
rossum.ai
- ?matches any single character (e.g.john?doe@rossum.aimatchesjohn.doe@rossum.aias well asjohn-doe@rossum.ai)
?
john?doe@rossum.ai
john.doe@rossum.ai
john-doe@rossum.ai
document_rejection_conditionsdefines rules for filtering incoming documents via email.
document_rejection_conditions
AttributeTypeDefaultDescriptionallowed_senderslist[string][]Only emails with matching sender's address will be processed. If empty all senders all allowed.denied_senderslist[string][]Incoming emails from email address matching one of these will be ignored.document_rejection_conditionsobject{}Rules for filtering out documents coming to Rossum smart inbox. Seedocument rejection conditions object
[]
[]
{}

#### Document rejection conditions object

This object configures filtering of documents Rossum received via its smart inbox. If it's enabled document will be rejected
once it satisfied at least one of defined conditions.
Setting attribute value to null (or empty list in case ofmime_types,file_name_regexes) will turn that specific filtering feature off.
mime_types
file_name_regexes
AttributeTypeDefaultDescriptionenabledbooltrueWhether the document rejection feature is enabled.resolution_lower_than_pxtuple[integer, integer][1200, 600]Resolution [width, height] in pixels. A file will be filtered out if both of the dimensions are smaller than the limits.file_size_less_than_bintegernullSize of document in bytes. A file with smaller size will be filtered out.mime_typeslist[string]["image/gif"]List of mime types to filter out (must match^.+/.+$).file_name_regexeslist[string]nullRegular expressions inre2format (for more info about syntax seedocs). A file with matching name will be filtered out.
true
[1200, 600]
null
["image/gif"]
^.+/.+$
null
re2

### List all inboxes

List all inboxes

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/inboxes'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/inboxes'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1234,"name":"Receipts","url":"https://<example>.rossum.app/api/v1/inboxes/1234","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"email":"east-west-trading-co-recepits@<example>.rossum.app","email_prefix":"east-west-trading-co-recepits","bounce_email_to":"bounces@east-west.com","bounce_unprocessable_attachments":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":true,"metadata":{},"filters":{"allowed_senders":[],"denied_senders":[]},"dmarc_check_action":"accept","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z"},{"id":1244,"name":"Beta Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-beta@<example>.rossum.app","email_prefix":"east-west-trading-co-beta","bounce_email_to":"bill@east-west.com","bounce_unprocessable_attachments":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":false,"metadata":{},"filters":{"allowed_senders":["*@east-west.com"],"denied_senders":[]},"dmarc_check_action":"accept""modified_by":null,"modified_at":null}]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1234,"name":"Receipts","url":"https://<example>.rossum.app/api/v1/inboxes/1234","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"email":"east-west-trading-co-recepits@<example>.rossum.app","email_prefix":"east-west-trading-co-recepits","bounce_email_to":"bounces@east-west.com","bounce_unprocessable_attachments":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":true,"metadata":{},"filters":{"allowed_senders":[],"denied_senders":[]},"dmarc_check_action":"accept","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z"},{"id":1244,"name":"Beta Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-beta@<example>.rossum.app","email_prefix":"east-west-trading-co-beta","bounce_email_to":"bill@east-west.com","bounce_unprocessable_attachments":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":false,"metadata":{},"filters":{"allowed_senders":["*@east-west.com"],"denied_senders":[]},"dmarc_check_action":"accept""modified_by":null,"modified_at":null}]}
GET /v1/inboxes
GET /v1/inboxes
Retrieve all inbox objects.
Supported filters:id,name,email,email_prefix,bounce_email_to,bounce_unprocessable_attachments,bounce_postponed_annotations,bounce_deleted_annotations
id
name
email
email_prefix
bounce_email_to
bounce_unprocessable_attachments
bounce_postponed_annotations
bounce_deleted_annotations
Supported ordering:id,name,email,email_prefix,bounce_email_to
id
name
email
email_prefix
bounce_email_to
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofinboxobjects.

### Create a new inbox

Create new inbox related to queue8236namedTest Inbox
8236

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Inbox", "email_prefix": "east-west-trading-co-test", "bounce_email_to": "joe@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"], "filters": {"allowed_senders": ["*@east-west-trading.com"]}}'\'https://<example>.rossum.app/api/v1/inboxes'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Inbox", "email_prefix": "east-west-trading-co-test", "bounce_email_to": "joe@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"], "filters": {"allowed_senders": ["*@east-west-trading.com"]}}'\'https://<example>.rossum.app/api/v1/inboxes'

```
{"id":1244,"name":"Test Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-test-b21e3a@<example>.rossum.app","email_prefix":"east-west-trading-co-test","bounce_email_to":"joe@east-west-trading.com","bounce_unprocessable_attachments":false,"bounce_postponed_annotations":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":true,"metadata":{},"filters":{"allowed_senders":["*@east-west-trading.com"],"denied_senders":[]},"dmarc_check_action":"accept","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z"}
```

{"id":1244,"name":"Test Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-test-b21e3a@<example>.rossum.app","email_prefix":"east-west-trading-co-test","bounce_email_to":"joe@east-west-trading.com","bounce_unprocessable_attachments":false,"bounce_postponed_annotations":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":true,"metadata":{},"filters":{"allowed_senders":["*@east-west-trading.com"],"denied_senders":[]},"dmarc_check_action":"accept","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z"}
POST /v1/inboxes
POST /v1/inboxes
Create a new inbox object.

#### Response

Status:201
201
Returns createdinboxobject.

### Retrieve an inbox

Get inbox object1244
1244

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/inboxes/1244'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/inboxes/1244'

```
{"id":1244,"name":"Test Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-beta@<example>.rossum.app",...}
```

{"id":1244,"name":"Test Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-beta@<example>.rossum.app",...}
GET /v1/inboxes/{id}
GET /v1/inboxes/{id}
Get an inbox object.

#### Response

Status:200
200
Returnsinboxobject.

### Update an inbox

Update inbox object1244
1244

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Shiny Inbox", "email": "east-west-trading-co-test@<example>.rossum.app", "bounce_email_to": "jack@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"]}'\'https://<example>.rossum.app/api/v1/inboxes/1244'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Shiny Inbox", "email": "east-west-trading-co-test@<example>.rossum.app", "bounce_email_to": "jack@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"]}'\'https://<example>.rossum.app/api/v1/inboxes/1244'

```
{"id":1244,"name":"Shiny Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-test@<example>.rossum.app","bounce_email_to":"jack@east-west-trading.com",...}
```

{"id":1244,"name":"Shiny Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-test@<example>.rossum.app","bounce_email_to":"jack@east-west-trading.com",...}
PUT /v1/inboxes/{id}
PUT /v1/inboxes/{id}
Update inbox object.

#### Response

Status:200
200
Returns updatedinboxobject.

### Update a part of an inbox

Update email of inbox object1244
1244

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Common Inbox"}'\'https://<example>.rossum.app/api/v1/inboxes/1244'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Common Inbox"}'\'https://<example>.rossum.app/api/v1/inboxes/1244'

```
{"id":1244,"name":"Common Inbox",...}
```

{"id":1244,"name":"Common Inbox",...}
PATCH /v1/inboxes/{id}
PATCH /v1/inboxes/{id}
Update a part of inbox object.

#### Response

Status:200
200
Returns updatedinboxobject.

### Delete an inbox

Delete inbox1244
1244

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/inboxes/1244'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/inboxes/1244'
DELETE /v1/inboxes/{id}
DELETE /v1/inboxes/{id}
Delete inbox object.

#### Response

Status:204
204


## Label

Example label object

```
{"id":1,"url":"https://<example>.rossum.app/api/v1/labels/1","name":"expedite","organization":"https://<example>.rossum.app/api/v1/organizationss/1","color":"#FF5733",}
```

{"id":1,"url":"https://<example>.rossum.app/api/v1/labels/1","name":"expedite","organization":"https://<example>.rossum.app/api/v1/organizationss/1","color":"#FF5733",}
Label object represents arbitrary labels added toannotationobjects.
AttributeTypeRead-onlyDefaultDescriptionidintegeryesLabel object ID.urlURLyesLabel object URL.namestringnoText of the label.organizationURLyesOrganization the label belongs to.colorstringnonullColor of the label in RGB hex format.
null

### List all labels

List all labels

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/labels'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/labels'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/labels/1",...}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/labels/1",...}]}
GET /v1/labels
GET /v1/labels
List all label objects.
Supported filters:id,name
id
name
Supported ordering:id,name
id
name
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list oflabelobjects.

### Retrieve label

Get label object123
123

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/labels/123'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/labels/123'

```
{"id":123,"url":"https://<example>.rossum.app/api/v1/labels/123",...}
```

{"id":123,"url":"https://<example>.rossum.app/api/v1/labels/123",...}
GET /v1/labels/{id}
GET /v1/labels/{id}
Retrieve a label object.

#### Response

Status:200
200
Returnslabelobject.

### Create a new label

Create new label

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "expedite"}'\'https://<example>.rossum.app/api/v1/labels'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "expedite"}'\'https://<example>.rossum.app/api/v1/labels'

```
{"id":42,"url":"https://<example>.rossum.app/api/v1/labels/42",...}
```

{"id":42,"url":"https://<example>.rossum.app/api/v1/labels/42",...}
POST /v1/labels
POST /v1/labels
Create a new label object.

#### Response

Status:201
201
Returns createdlabelobject.

### Update part of a label

Update content of label object42
42

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Unreadable"}'\'https://<example>.rossum.app/api/v1/labels/42'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Unreadable"}'\'https://<example>.rossum.app/api/v1/labels/42'

```
{"id":42,"url":"https://<example>.rossum.app/api/v1/labels/42",...}
```

{"id":42,"url":"https://<example>.rossum.app/api/v1/labels/42",...}
PATCH /v1/labels/{id}
PATCH /v1/labels/{id}
Update part of label object.

#### Response

Status:200
200
Returns updatedlabelobject.

### Update a label

Update label object42
42

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "postpone"}'\'https://<example>.rossum.app/api/v1/labels/42'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "postpone"}'\'https://<example>.rossum.app/api/v1/labels/42'

```
{"id":42,"url":"https://<example>.rossum.app/api/v1/labels/42",...}
```

{"id":42,"url":"https://<example>.rossum.app/api/v1/labels/42",...}
PUT /v1/labels/{id}
PUT /v1/labels/{id}
Update label object.

#### Response

Status:200
200
Returns updatedlabelobject.

### Delete a label

Delete label42
42

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/labels/42'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/labels/42'
DELETE /v1/labels/{id}
DELETE /v1/labels/{id}
Delete label object.

#### Response

Status:204
204

### Add/Remove labels on annotations

Add label42, remove label43to annotations10,11
42
43
10
11

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"operations": {"add": ["https://<example>.rossum.app/api/v1/labels/42"], \
                      "remove": ["https://<example>.rossum.app/api/v1/labels/43"]}, \
  "objects": {"annotations": ["https://<example>.rossum.app/api/v1/annotations/10", \
                              "https://<example>.rossum.app/api/v1/annotations/11"]}}'\'https://<example>.rossum.app/api/v1/labels/apply'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"operations": {"add": ["https://<example>.rossum.app/api/v1/labels/42"], \
                      "remove": ["https://<example>.rossum.app/api/v1/labels/43"]}, \
  "objects": {"annotations": ["https://<example>.rossum.app/api/v1/annotations/10", \
                              "https://<example>.rossum.app/api/v1/annotations/11"]}}'\'https://<example>.rossum.app/api/v1/labels/apply'
POST /v1/labels/apply
POST /v1/labels/apply
Add/Remove labels on annotations.

#### Response

Status:204
204


## Membership

Example membership object

```
{"id":3,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/3","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/4","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/3","https://<example>.rossum.app/api/v1/organization_groups/1/queues/4"],"expires_at":null}
```

{"id":3,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/3","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/4","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/3","https://<example>.rossum.app/api/v1/organization_groups/1/queues/4"],"expires_at":null}
Membership represents a relation between user, organization (besides its primary organization) and queues.
It provides a way how users can work with multiple organizations within the same organization group. Using
memberships one can query the resources from a different organization the same way how one would do in
their own organization. To do so, a membership shall becreatedfirst, then
a membership token shall begenerated. Such token then
can be used in any subsequent calls made to the target organization.
organization_group_admin
AttributeTypeDefaultDescriptionidintegerId of the membershipurlURLURL of the membershipuserURLURL of the userorganizationURLURL of the organizationqueueslist[URL]URLs of queues user has access toexpires_atdatetimenullTimestamp of membership expiration. Membership won't expire if no expiration is set.

### List all memberships

List all memberships in organization group1
1

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/1/memberships'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/1/memberships'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":3,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/3","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/4","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/1","https://<example>.rossum.app/api/v1/organization_groups/1/queues/2"],"expires_at":null},{"id":4,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/4","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/5","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/1"],"expires_at":null}]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":3,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/3","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/4","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/1","https://<example>.rossum.app/api/v1/organization_groups/1/queues/2"],"expires_at":null},{"id":4,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/4","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/5","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/1"],"expires_at":null}]}
GET /v1/organization_groups/{id}/memberships
GET /v1/organization_groups/{id}/memberships
Retrieve all membership objects.
Supported filters:user,organization
user
organization
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofmembershipobjects.

### Retrieve a membership

Get membership object with ID4in organization group1
4
1

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/1/memberships/4'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/1/memberships/4'

```
{"id":4,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/4","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/5","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/1"],"expires_at":null}
```

{"id":4,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/4","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/5","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/1"],"expires_at":null}
GET /v1/organization_groups/{id}/memberships/{id}
GET /v1/organization_groups/{id}/memberships/{id}
Get a membership object.

#### Response

Status:200
200
Returnsmembershipobject.

### Create new membership

Create new membership

```
curl-s-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{ \
        "user": "https://<example>.rossum.app/api/v1/organization_groups/2/users/6", \
        "organization": "https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5", \
        "queues": ["https://<example>.rossum.app/api/v1/organization_groups/2/queues/6"]
        }''https://<example>.rossum.app/api/v1/organization_groups/2/memberships'
```

curl-s-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{ \
        "user": "https://<example>.rossum.app/api/v1/organization_groups/2/users/6", \
        "organization": "https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5", \
        "queues": ["https://<example>.rossum.app/api/v1/organization_groups/2/queues/6"]
        }''https://<example>.rossum.app/api/v1/organization_groups/2/memberships'

```
{"id":5,"url":"https://<example>.rossum.app/api/v1/organization_groups/2/memberships/5","user":"https://<example>.rossum.app/api/v1/organization_groups/2/users/6","organization":"https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5","queues":[],"expires_at":null}
```

{"id":5,"url":"https://<example>.rossum.app/api/v1/organization_groups/2/memberships/5","user":"https://<example>.rossum.app/api/v1/organization_groups/2/users/6","organization":"https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5","queues":[],"expires_at":null}
POST /v1/organization_groups/{id}/memberships
POST /v1/organization_groups/{id}/memberships
Create a membership object.

#### Response

Status:201
201
Returnsmembershipobject.

### Partially update membership

Partially update membership with ID7in organization group2
7
2

```
curl-s-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"queues": ["https://<example>.rossum.app/api/v1/organization_groups/2/queues/6"]}'\'https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7'
```

curl-s-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"queues": ["https://<example>.rossum.app/api/v1/organization_groups/2/queues/6"]}'\'https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7'

```
{"id":7,"url":"https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7","user":"https://<example>.rossum.app/api/v1/organization_groups/2/users/6","organization":"https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/2/queues/6"],"expires_at":null}
```

{"id":7,"url":"https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7","user":"https://<example>.rossum.app/api/v1/organization_groups/2/users/6","organization":"https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/2/queues/6"],"expires_at":null}
PATCH /v1/organization_groups/{id}/memberships/{id}
PATCH /v1/organization_groups/{id}/memberships/{id}
Update a part of membership object.

#### Response

Status:200
200
Returnsmembershipobject.

### Update membership

Update membership with ID7in organization group2
7
2

```
curl-s-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{ \
    "user": "https://<example>.rossum.app/api/v1/organization_groups/2/users/7", \
    "organization": "https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5", \
    "queues": ["https://<example>.rossum.app/api/v1/organization_groups/2/queues/12"]
    }''https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7'
```

curl-s-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{ \
    "user": "https://<example>.rossum.app/api/v1/organization_groups/2/users/7", \
    "organization": "https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5", \
    "queues": ["https://<example>.rossum.app/api/v1/organization_groups/2/queues/12"]
    }''https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7'

```
{"id":7,"url":"https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7","user":"https://<example>.rossum.app/api/v1/organization_groups/2/users/7","organization":"https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/2/queues/12"],"expires_at":null}
```

{"id":7,"url":"https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7","user":"https://<example>.rossum.app/api/v1/organization_groups/2/users/7","organization":"https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/2/queues/12"],"expires_at":null}
PUT /v1/organization_groups/{id}/memberships/{id}
PUT /v1/organization_groups/{id}/memberships/{id}
Update a membership object.

#### Response

Status:200
200
Returnsmembershipobject.

### Delete membership

Delete membership with ID7in organization group2
7
2

```
curl-s-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7'
```

curl-s-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7'
DELETE /v1/organization_groups/{id}/memberships/{id}
DELETE /v1/organization_groups/{id}/memberships/{id}
Delete a membership object.

#### Response

Status:204
204


## Note

Example note object

```
{"id":1,"url":"https://<example>.rossum.app/api/v1/notes/1","type":"rejection","metadata":{},"content":"Arbitrary note text","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T10:08:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/1"}
```

{"id":1,"url":"https://<example>.rossum.app/api/v1/notes/1","type":"rejection","metadata":{},"content":"Arbitrary note text","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T10:08:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/1"}
Note object represents arbitrary notes added toannotationobjects.
AttributeTypeRead-onlyDescriptionidintegeryesNote object ID.urlURLyesNote object URL.metadataobjectnoClient data.contentstring (max. 4096 chars)noNote's string content.created_atdatetimeyesTimestamp of object's creation.creatorURLyesUser that created the note.modified_atdatetimeyesTimestamp of last modification.modifierURLyesUser that last modified the note.modified_byURLyesUser that last modified the note.annotationURLnoAnnotation the note belongs to.typestringnoNote type. Possible values:rejection.
rejection

### List all notes

List all notes

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/notes'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/notes'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/notes/1","type":"rejection","metadata":{},"content":"Arbitrary note text","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T10:08:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/1"}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/notes/1","type":"rejection","metadata":{},"content":"Arbitrary note text","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T10:08:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/1"}]}
GET /v1/notes
GET /v1/notes
List all note objects.
Supported filters:annotation,creator
annotation
creator
Supported ordering:modified_at,created_at
modified_at
created_at
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofnoteobjects.

### Retrieve note

Get note object123
123

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/notes/123'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/notes/123'

```
{"id":123,"url":"https://<example>.rossum.app/api/v1/notes/123","type":"rejection","metadata":{},"content":"Arbitrary note text","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T10:08:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/12","modified_by":"https://<example>.rossum.app/api/v1/users/12","annotation":"https://<example>.rossum.app/api/v1/annotations/150"}
```

{"id":123,"url":"https://<example>.rossum.app/api/v1/notes/123","type":"rejection","metadata":{},"content":"Arbitrary note text","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T10:08:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/12","modified_by":"https://<example>.rossum.app/api/v1/users/12","annotation":"https://<example>.rossum.app/api/v1/annotations/150"}
GET /v1/notes/{id}
GET /v1/notes/{id}
Retrieve a note object.

#### Response

Status:200
200
Returnsnoteobject.

### Create a new note

Create new note related to annotation45
45

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": "Does not have invoice ID", "type": "rejection", "annotation": "https://<example>.rossum.app/api/v1/annotations/45"}'\'https://<example>.rossum.app/api/v1/notes'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": "Does not have invoice ID", "type": "rejection", "annotation": "https://<example>.rossum.app/api/v1/annotations/45"}'\'https://<example>.rossum.app/api/v1/notes'

```
{"id":42,"url":"https://<example>.rossum.app/api/v1/notes/42","type":"rejection","metadata":{},"content":"Does not have invoice ID","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":null,"modifier":null,"modified_by":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/45"}
```

{"id":42,"url":"https://<example>.rossum.app/api/v1/notes/42","type":"rejection","metadata":{},"content":"Does not have invoice ID","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":null,"modifier":null,"modified_by":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/45"}
POST /v1/notes
POST /v1/notes
Create a new note object.

#### Response

Status:201
201
Returns creatednoteobject.

### Update part of a note

Update content of note object42
42

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": "Unreadable"}'\'https://<example>.rossum.app/api/v1/notes/42'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": "Unreadable"}'\'https://<example>.rossum.app/api/v1/notes/42'

```
{"id":42,"url":"https://<example>.rossum.app/api/v1/notes/42","type":"rejection","metadata":{},"content":"Unreadable","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T011:10:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/45"}
```

{"id":42,"url":"https://<example>.rossum.app/api/v1/notes/42","type":"rejection","metadata":{},"content":"Unreadable","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T011:10:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/45"}
PATCH /v1/notes/{id}
PATCH /v1/notes/{id}
Update part of note object.

#### Response

Status:200
200
Returns updatednoteobject.

### Update a note

Update note object42
42

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "rejection", "content": "Misspelled vendor ID", "annotation": "https://<example>.rossum.app/api/v1/annotations/45"}'\'https://<example>.rossum.app/api/v1/notes/42'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "rejection", "content": "Misspelled vendor ID", "annotation": "https://<example>.rossum.app/api/v1/annotations/45"}'\'https://<example>.rossum.app/api/v1/notes/42'

```
{"id":42,"url":"https://<example>.rossum.app/api/v1/notes/42","type":"rejection","metadata":{},"content":"Misspelled vendor ID","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T011:10:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/45"}
```

{"id":42,"url":"https://<example>.rossum.app/api/v1/notes/42","type":"rejection","metadata":{},"content":"Misspelled vendor ID","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T011:10:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/45"}
PUT /v1/notes/{id}
PUT /v1/notes/{id}
Update note object.

#### Response

Status:200
200
Returns updatednoteobject.

### Delete a note

Delete note42
42

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/notes/42'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/notes/42'
DELETE /v1/notes/{id}
DELETE /v1/notes/{id}
Delete note object.

#### Response

Status:204
204


## Organization

Example organization object

```
{"id":406,"url":"https://<example>.rossum.app/api/v1/organizations/406","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/7540"],"users":["https://<example>.rossum.app/api/v1/users/10775"],"organization_group":"https://<example>.rossum.app/api/v1/organization_groups/17","ui_settings":{},"metadata":{},"created_at":"2019-09-02T14:28:11.000000Z","trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"oidc_provider":null,"internal_info":{"cs_account_classification":null,"customer_type":null,"market_category":null,"overdue_payment_date":null,"sso_active":false},"creator":"https://<example>.rossum.app/api/v1/users/10775","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":406,"url":"https://<example>.rossum.app/api/v1/organizations/406","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/7540"],"users":["https://<example>.rossum.app/api/v1/users/10775"],"organization_group":"https://<example>.rossum.app/api/v1/organization_groups/17","ui_settings":{},"metadata":{},"created_at":"2019-09-02T14:28:11.000000Z","trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"oidc_provider":null,"internal_info":{"cs_account_classification":null,"customer_type":null,"market_category":null,"overdue_payment_date":null,"sso_active":false},"creator":"https://<example>.rossum.app/api/v1/users/10775","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
Organization is a basic unit that contains all objects that are required to fully use Rossum platform.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the organizationtruenamestringName of the organization (not visible in UI)urlURLURL of the organizationtrueworkspaceslist[URL]List of workspaces objects in the organizationtrueuserslist[URL]List of users in the organizationtrueorganization_groupURLURL to organization group the organization belongs totrueui_settingsobject{}Organization-wide frontend UI settings (e.g. locales). Rossum internal.metadataobject{}Client data.is_trialboolProperty indicates whether this license is a trial licensetruecreated_attimestampTimestamp for when the organization was createdtruetrial_expires_attimestampTimestamp for when the trial period ended (ISO 8601)trueoidc_providerstringnull(Deprecated) OpenID Connect provider nametrueinternal_infoobjectnullINTERNALRossum internal information on organization.truecreatorURLnullURL of the first user of the organization (set during organization creation)truemodified_byURLnullURL of the last modifiertruemodified_atdatetimenullDate of the last modificationtruesettingsobject{}Settings of the organization (seeorganization settings)falsesandboxboolFalseSpecifies if the organization is a sandboxfalse
{}
{}
{}

#### Organization settings

AttributeTypeDescriptionDefaultannotation_list_tableobjectConfiguration of annotation dashboard columns{}
{}

### Create new organization


```
curl-s-XPOST-H'Content-Type: application/json'\-d'{"template_name": "UK Demo Template", "organization_name": "East West Trading Co", "user_fullname": "John Doe", "user_email": "john@east-west-trading.com", "user_password": "owo1aiG9ua9Aihai", "user_ui_settings": { "locale": "en" }, "create_key": "13156106d6f185df24648ac7ff20f64f1c5c06c144927be217189e26f8262c4a", "domain": "acme-corp"}'\'https://<example>.rossum.app/api/v1/organizations/create'
```

curl-s-XPOST-H'Content-Type: application/json'\-d'{"template_name": "UK Demo Template", "organization_name": "East West Trading Co", "user_fullname": "John Doe", "user_email": "john@east-west-trading.com", "user_password": "owo1aiG9ua9Aihai", "user_ui_settings": { "locale": "en" }, "create_key": "13156106d6f185df24648ac7ff20f64f1c5c06c144927be217189e26f8262c4a", "domain": "acme-corp"}'\'https://<example>.rossum.app/api/v1/organizations/create'

```
{"organization":{"id":105,"url":"https://<example>.rossum.app/api/v1/organizations/105","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/160"],"users":["https://<example>.rossum.app/api/v1/users/173"],"organization_group":"https://<example>.rossum.app/api/v1/organization_groups/17","ui_settings":{},"metadata":{},"trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"oidc_provider":null,"domain":"acme-corp","phone_number":"721722723","communication_opt_in":false,"creator":"https://<example>.rossum.app/api/v1/users/173"}}
```

{"organization":{"id":105,"url":"https://<example>.rossum.app/api/v1/organizations/105","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/160"],"users":["https://<example>.rossum.app/api/v1/users/173"],"organization_group":"https://<example>.rossum.app/api/v1/organization_groups/17","ui_settings":{},"metadata":{},"trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"oidc_provider":null,"domain":"acme-corp","phone_number":"721722723","communication_opt_in":false,"creator":"https://<example>.rossum.app/api/v1/users/173"}}
POST /v1/organizations/create
POST /v1/organizations/create
Create new organization and related objects (workspace, queue, user, schema, inbox, domain).
AttributeTypeDefaultDescriptionRequiredtemplate_nameenumTemplate to use for new organization (see below)trueorganization_namestringName of the organization. Will be also used as a base for inbox e-mail address.trueuser_fullnamestringFull user nametrueuser_emailEMAILValid email of the user (also used as Rossum login)trueuser_passwordstring*generatedInitial user passworduser_ui_settingsobject{"locale": "en"}Initial UI settingscreate_keystringA key that allows to create an organizationtrue
You need acreate_keyin order to create an organization. Please contactsupport@rossum.aito obtain one.
create_key
Selectedtemplate_nameaffects default schema and extracted fields. Please
note that the demo templates may be updated as new features are introduced.
template_name
Available templates:
Template nameDescriptionIs demoEmpty Organization TemplateEmpty organization, suitable for further customizationnoCZ Demo TemplateCzech standard invoicesyesTax Invoice EU Demo TemplateVAT Invoices, Credit Notes, Debit Notes, Purchase/Sales Orders, Receipts, and Pro Formas coming from the EUyesTax Invoice US Demo TemplateTax Invoices, Credit Notes, Debit Notes, Purchase/Sales Orders, Receipts, and Pro Formas coming from the USyesTax Invoice UK Demo TemplateVAT Invoices, Credit Notes, Debit Notes, Purchase/Sales Orders, Receipts, and Pro Formas coming from the UK, India, Canada, or AustraliayesDelivery Note Demo TemplateDelivery NotesyesTax Invoice CN Demo Templategovernmental Tax Invoices from Mainland China (fapiaos)yesCertificates of Analysis Demo TemplateCertificates of Analysis that are quality control documents common in the food and beverage industryyes

#### Response

Status:201
201
Returns object withorganizationkey andorganizationobject value.
organization

### Organization limits

Used to get information about various limits in regard to Organization.
Get Organization limits.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/5/limits'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/5/limits'

```
{"email_limits":{"count_today":7,"count_today_notification":4,"count_total":9,"email_per_day_limit":10,"email_per_day_limit_notification":10,"email_total_limit":20,"last_sent_at":"2022-01-13","last_sent_at_notification":"2022-01-13"}}
```

{"email_limits":{"count_today":7,"count_today_notification":4,"count_total":9,"email_per_day_limit":10,"email_per_day_limit_notification":10,"email_total_limit":20,"last_sent_at":"2022-01-13","last_sent_at_notification":"2022-01-13"}}
GET /v1/organizations/{id}/limits
GET /v1/organizations/{id}/limits

#### Response

Status:200
200
The response currently consists only ofemail_limits.
email_limits
AttributeTypeDescriptioncount_todayintegerEmails sent by user today count.count_today_notificationintegerNotification emails sent today count.count_totalintegerEmails sent by user total count.email_per_day_limitintegerEmails sent by user today limit.email_per_day_limit_notificationintegerNotification emails sent today limit.email_total_limitintegerEmails sent by user total limit.last_sent_atdateDate of last sent email.last_sent_at_notificationdateDate of last sent notification.

### List all organizations

List all organizations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":406,"url":"https://<example>.rossum.app/api/v1/organizations/406","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/7540"],"users":["https://<example>.rossum.app/api/v1/users/10775"],"organization_group":"https://<example>.rossum.app/api/v1/organization_groups/17","ui_settings":{},"metadata":{},"created_at":"2019-09-02T14:28:11.000000Z","trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"internal_info":{"cs_account_classification":null,"customer_type":null,"market_category":null,"overdue_payment_date":null},"creator":"https://<example>.rossum.app/api/v1/users/10775","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":406,"url":"https://<example>.rossum.app/api/v1/organizations/406","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/7540"],"users":["https://<example>.rossum.app/api/v1/users/10775"],"organization_group":"https://<example>.rossum.app/api/v1/organization_groups/17","ui_settings":{},"metadata":{},"created_at":"2019-09-02T14:28:11.000000Z","trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"internal_info":{"cs_account_classification":null,"customer_type":null,"market_category":null,"overdue_payment_date":null},"creator":"https://<example>.rossum.app/api/v1/users/10775","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
GET /v1/organizations
GET /v1/organizations
Retrieve all organization objects.
Supported filters:id,name
id
name
Supported ordering:id,name
id
name
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list oforganizationobjects. Usually, there would only be one organization.

### Retrieve an organization

Get organization object406
406

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/406'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/406'

```
{"id":406,"url":"https://<example>.rossum.app/api/v1/organizations/406","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/7540"],"users":["https://<example>.rossum.app/api/v1/users/10775"],"ui_settings":{},"metadata":{},"created_at":"2019-09-02T14:28:11.000000Z","trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"internal_info":{"cs_account_classification":null,"customer_type":null,"market_category":null,"overdue_payment_date":null},"creator":"https://<example>.rossum.app/api/v1/users/10775","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":406,"url":"https://<example>.rossum.app/api/v1/organizations/406","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/7540"],"users":["https://<example>.rossum.app/api/v1/users/10775"],"ui_settings":{},"metadata":{},"created_at":"2019-09-02T14:28:11.000000Z","trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"internal_info":{"cs_account_classification":null,"customer_type":null,"market_category":null,"overdue_payment_date":null},"creator":"https://<example>.rossum.app/api/v1/users/10775","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
GET /v1/organizations/{id}
GET /v1/organizations/{id}
Get an organization object.

#### Response

Status:200
200
Returnsorganizationobject.

### Generate a token to access the organization

Generate a token for organization 406

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/auth/membership_token'-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406"}'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/auth/membership_token'-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406"}'

```
{"key":"b6dde6e6280c697bc4afac7f920c5cee8c9c9t7d","organization":"https://<example>.rossum.app/api/v1/organizations/406"}
```

{"key":"b6dde6e6280c697bc4afac7f920c5cee8c9c9t7d","organization":"https://<example>.rossum.app/api/v1/organizations/406"}
POST /v1/auth/membership_token
POST /v1/auth/membership_token
Generate token for access to membership and primary organizations. If the user is a group administrator, token can be generated for any organization in his organization group.
AttributeTypeDescriptionRequiredorganizationURLURL to theorganizationto which the token will have accessYesoriginstringFor internal use only. Using this field may affectthrottlingof your API requests.No

#### Response

Status:200
200
Returns object withkey(authorization token belonging to requested organization) andorganizationURL.
key

### Retrieve all membership organizations

Get organizations the user is a member of

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations?include_membership_organizations=true'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations?include_membership_organizations=true'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":741924,"url":"https://<example>.rossum.app/api/v1/organizations/741924","name":"Best organization",...},...]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":741924,"url":"https://<example>.rossum.app/api/v1/organizations/741924","name":"Best organization",...},...]}
GET /v1/organizations?include_membership_organizations=true
GET /v1/organizations?include_membership_organizations=true
Returnspaginatedresponse with a list of organizations that user is either in or is connected to through membership. If user isorganization group admin, he can list all the organizations from the organization group.
organization group admin

#### Response

Status:200
200
Returns list oforganizationobjects.

### Billing for organization


#### Billing stats for organization

In order to obtain an overview of the billed items, you can get basic billing statistics.
Download billing stats report (August 1, 2021 - August 31, 2021).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-08-01", "end_date": "2021-08-31", "queues": [
      "https://<example>.rossum.app/api/v1/queues/8199"]}, "group_by": ["queue"]}'\'https://<example>.rossum.app/api/v1/organizations/789/billing_stats'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-08-01", "end_date": "2021-08-31", "queues": [
      "https://<example>.rossum.app/api/v1/queues/8199"]}, "group_by": ["queue"]}'\'https://<example>.rossum.app/api/v1/organizations/789/billing_stats'
POST /v1/organizations/{id}/billing_stats
POST /v1/organizations/{id}/billing_stats
AttributeTypeDescriptionfiltersobjectFilters used for the computation of billed items counts (seebilling stats filters)group_bylist[string]List of attributes by which theresultsare to be grouped. Only a single value is supported. Possible values:queue,monthandweek.order_bylist[string]List of attributes by which theresultsare to be ordered. Possible values:billable_pages,billable_documents,non_billable_pages,non_billable_pages
results
queue
month
week
results
billable_pages
billable_documents
non_billable_pages
non_billable_pages
AttributeTypeDescriptionqueueslist[URL]Filter billed items for the specified queues (ornullfor historically deleted queues) to be counted to the reportbegin_datedatetimeFilter billed items that was issuedsincethe specified date (including the specified date) to be counted to the report.end_datedatetimeFilter billed items that was issuedup tothe specified date (including the specified date) to be counted to the report.
null
Status:200
200

```
{"pagination":{"next":null,"previous":null,"total":11,"total_pages":1},"results":[{"begin_date":"2021-10-01","end_date":"2021-10-31","organization":"https://<example>.rossum.app/api/v1/organizations/406","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"billable_documents":13,"billable_pages":7,"non_billable_documents":0,"non_billable_pages":0}},{"begin_date":"2021-12-01","end_date":"2021-12-31","organization":"https://<example>.rossum.app/api/v1/organizations/406","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"billable_documents":5,"billable_pages":5,"non_billable_documents":0,"non_billable_pages":0}},...],"totals":{"billable_documents":21288,"billable_pages":30204,"non_billable_documents":81,"non_billable_pages":5649},"updated_at":"2022-09-01"}
```

{"pagination":{"next":null,"previous":null,"total":11,"total_pages":1},"results":[{"begin_date":"2021-10-01","end_date":"2021-10-31","organization":"https://<example>.rossum.app/api/v1/organizations/406","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"billable_documents":13,"billable_pages":7,"non_billable_documents":0,"non_billable_pages":0}},{"begin_date":"2021-12-01","end_date":"2021-12-31","organization":"https://<example>.rossum.app/api/v1/organizations/406","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"billable_documents":5,"billable_pages":5,"non_billable_documents":0,"non_billable_pages":0}},...],"totals":{"billable_documents":21288,"billable_pages":30204,"non_billable_documents":81,"non_billable_pages":5649},"updated_at":"2022-09-01"}
paginatedresponse with a list ofbilling stats resultsobjects and atotalsobject.
Totalscontain summary information for the whole period (betweenbegin_dateandend_date). The contract defines
the billing unit (pagesordocuments).
Totals
begin_date
end_date
pages
documents
AttributeTypeDescriptionbillable_documentsintNumber of documents billed.billable_pagesintNumber of pages billed.non_billable_documentsintNumber of documents that were received but not billed.non_billable_pagesintNumber of pages that were received but not billed.
Resultscontain information grouped by fields defined ingroup_by. The data (seeabove)
are wrapped invaluesobject, and accompanied by the values of attributes that were used for grouping.
Results
group_by
values
AttributeTypeDescriptionqueueURLBilled pages or documents QueueorganizationURLBilled pages or documents Organizationbegin_datedateStart date of the pages or documents billing info within the groupend_datedateFinal date of the pages or documents billing info within the groupvaluesobjectContains the data oftotalslist grouped by thegroup_by.
totals
group_by

#### Billing history for organization

Retrieve billing history report.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organizations/42/billing_history'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organizations/42/billing_history'
GET /v1/organizations/{id}/billing_history
GET /v1/organizations/{id}/billing_history
Retrieve billing history with entries corresponding to individual contracted periods. The valuepuchased_documentsorpurchased_pagesdefine the period billing unit.
puchased_documents
purchased_pages
Status:200
200

```
{"pagination":{"next":null,"previous":null,"total":2,"total_pages":1},"results":[{"begin_date":"2021-01-01","end_date":"2022-12-31","values":{"billable_documents":0,"non_billable_documents":0,"billable_pages":34735,"non_billable_pages":20,"is_current":true,"purchased_documents":0,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}},{"begin_date":"2020-01-01","end_date":"2021-12-31","values":{"billable_documents":10209,"non_billable_documents":20,"billable_pages":0,"non_billable_pages":0,"is_current":false,"purchased_documents":111,"purchased_pages":0,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}}],"totals":{"billable_documents":10209,"non_billable_documents":20,"billable_pages":34735,"non_billable_pages":20,"purchased_documents":111,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0},"updated_at":"2022-09-01"}
```

{"pagination":{"next":null,"previous":null,"total":2,"total_pages":1},"results":[{"begin_date":"2021-01-01","end_date":"2022-12-31","values":{"billable_documents":0,"non_billable_documents":0,"billable_pages":34735,"non_billable_pages":20,"is_current":true,"purchased_documents":0,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}},{"begin_date":"2020-01-01","end_date":"2021-12-31","values":{"billable_documents":10209,"non_billable_documents":20,"billable_pages":0,"non_billable_pages":0,"is_current":false,"purchased_documents":111,"purchased_pages":0,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}}],"totals":{"billable_documents":10209,"non_billable_documents":20,"billable_pages":34735,"non_billable_pages":20,"purchased_documents":111,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0},"updated_at":"2022-09-01"}

#### Billing stats export for organization

Download billing stats CSV report (Sep 1, 2021 - August 31, 2022).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-10-01", "end_date": "2022-09-31"}, "group_by": ["month"]}'\'https://<example>.rossum.app/api/v1/organizations/406/billing_stats/export'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-10-01", "end_date": "2022-09-31"}, "group_by": ["month"]}'\'https://<example>.rossum.app/api/v1/organizations/406/billing_stats/export'
POST /v1/organizations/{id}/billing_stats/export
POST /v1/organizations/{id}/billing_stats/export
Download the data provided by thebilling stats response resourcein a CSV output.
Status:200
200

```
begin_date,end_date,billable_pages,non_billable_pages,billable_documents,non_billable_documents
2021-10-01,2021-10-31,27,0,32,0
2021-11-01,2021-11-30,159,0,147,9
2021-12-01,2021-12-31,41,0,20,0
2022-01-01,2022-01-31,143,0,113,0
2022-02-01,2022-02-28,275,0,134,0
2022-03-01,2022-03-31,57,0,44,0
2022-04-01,2022-04-30,145,0,83,1
2022-05-01,2022-05-31,53,0,17,0
2022-06-01,2022-06-30,26837,5586,18061,18
2022-07-01,2022-07-31,3033,63,3014,64
2022-08-01,2022-08-31,347,0,101,0
2022-09-01,2022-09-31,117,0,28,4
```

begin_date,end_date,billable_pages,non_billable_pages,billable_documents,non_billable_documents
2021-10-01,2021-10-31,27,0,32,0
2021-11-01,2021-11-30,159,0,147,9
2021-12-01,2021-12-31,41,0,20,0
2022-01-01,2022-01-31,143,0,113,0
2022-02-01,2022-02-28,275,0,134,0
2022-03-01,2022-03-31,57,0,44,0
2022-04-01,2022-04-30,145,0,83,1
2022-05-01,2022-05-31,53,0,17,0
2022-06-01,2022-06-30,26837,5586,18061,18
2022-07-01,2022-07-31,3033,63,3014,64
2022-08-01,2022-08-31,347,0,101,0
2022-09-01,2022-09-31,117,0,28,4

#### Billing history export for organization

Download billing history CSV report.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organizations/406/billing_history/export'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organizations/406/billing_history/export'
GET /v1/organizations/{id}/billing_history/export
GET /v1/organizations/{id}/billing_history/export
Download the data provided by thebilling history response resourcein a CSV output.

#### Response

Status:200
200

```
begin_date,end_date,purchased_pages,billable_pages,non_billable_pages,purchased_documents,billable_documents,non_billable_documents,extracted_pages_with_learning,extracted_pages_without_learning,split_pages_with_learning,split_pages_without_learning,extracted_documents_with_learning,extracted_documents_without_learning,split_documents_with_learning,split_documents_without_learning,ocr_only_pages,ocr_only_documents,purchased_extracted_pages_with_learning,purchased_extracted_pages_without_learning,purchased_split_pages_with_learning,purchased_split_pages_without_learning,purchased_extracted_documents_with_learning,purchased_extracted_documents_without_learning,purchased_split_documents_with_learning,purchased_split_documents_without_learning,purchased_ocr_only_pages,purchased_ocr_only_documents
2021-01-01,2022-12-31,555,34735,100,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2020-01-01,2021-12-31,0,0,0,111,10209,123,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
```

begin_date,end_date,purchased_pages,billable_pages,non_billable_pages,purchased_documents,billable_documents,non_billable_documents,extracted_pages_with_learning,extracted_pages_without_learning,split_pages_with_learning,split_pages_without_learning,extracted_documents_with_learning,extracted_documents_without_learning,split_documents_with_learning,split_documents_without_learning,ocr_only_pages,ocr_only_documents,purchased_extracted_pages_with_learning,purchased_extracted_pages_without_learning,purchased_split_pages_with_learning,purchased_split_pages_without_learning,purchased_extracted_documents_with_learning,purchased_extracted_documents_without_learning,purchased_split_documents_with_learning,purchased_split_documents_without_learning,purchased_ocr_only_pages,purchased_ocr_only_documents
2021-01-01,2022-12-31,555,34735,100,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2020-01-01,2021-12-31,0,0,0,111,10209,123,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0

#### Billing for organization

In order to obtain an overview of the billed items, you can get basic billing statistics.
Download billing report (August 1, 2021 - August 31, 2021).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filter": {"begin_date": "2021-08-01", "end_date": "2021-08-31", "queues": [
      "https://<example>.rossum.app/api/v1/queues/8199"]}, "group_by": ["queue"]}'\'https://<example>.rossum.app/api/v1/organizations/789/billing'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filter": {"begin_date": "2021-08-01", "end_date": "2021-08-31", "queues": [
      "https://<example>.rossum.app/api/v1/queues/8199"]}, "group_by": ["queue"]}'\'https://<example>.rossum.app/api/v1/organizations/789/billing'
POST /v1/organizations/{id}/billing
POST /v1/organizations/{id}/billing
AttributeTypeDescriptionfilterobjectFilters used for the computation of billed items countsfilter.queueslist[URL]Filter billed items for the specified queues to be counted to the reportfilter.begin_datedatetimeFilter billed items that was issuedsincethe specified date (including the specified date) to be counted to the report.filter.end_datedatetimeFilter billed items that was issuedup tothe specified date (including the specified date) to be counted to the report.group_bylist[string]List of attributes by which theseriesis to be grouped. Possible values:queue.
series
queue

#### Response

Status:200
200

```
{"series":[{"begin_date":"2019-02-01","end_date":"2019-02-01","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"header_fields_per_page":2,"header_fields_per_document":5,"header_fields_and_line_items_per_page":9,"header_fields_and_line_items_per_document":20}},{"begin_date":"2019-02-02","end_date":"2019-02-02","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"header_fields_per_page":2,"header_fields_per_document":5,"header_fields_and_line_items_per_page":9,"header_fields_and_line_items_per_document":20}},,...],"totals":{"header_fields_per_page":8,"header_fields_per_document":16,"header_fields_and_line_items_per_page":20,"header_fields_and_line_items_per_document":43}}
```

{"series":[{"begin_date":"2019-02-01","end_date":"2019-02-01","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"header_fields_per_page":2,"header_fields_per_document":5,"header_fields_and_line_items_per_page":9,"header_fields_and_line_items_per_document":20}},{"begin_date":"2019-02-02","end_date":"2019-02-02","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"header_fields_per_page":2,"header_fields_per_document":5,"header_fields_and_line_items_per_page":9,"header_fields_and_line_items_per_document":20}},,...],"totals":{"header_fields_per_page":8,"header_fields_per_document":16,"header_fields_and_line_items_per_page":20,"header_fields_and_line_items_per_document":43}}
The response consists of two parts:totalsandseries.
totals
series

#### Billing totals

Totalscontain summary information for the whole period (betweenbegin_dateandend_date).
Totals
begin_date
end_date
AttributeTypeDescriptionheader_fields_per_pageintNumber of pages that were processed by Rossum AI Engine and where only header fields were supposed to be captured.header_fields_per_documentintNumber of documents that were processed by Rossum AI Engine and where only header fields were supposed to be captured.header_fields_and_line_items_per_pageintNumber of pages that were processed by Rossum AI Engine and where line item fields were supposed to be captured.header_fields_and_line_items_per_documentintNumber of documents that were processed by Rossum AI Engine and where line item fields were supposed to be captured.

#### Billing series

Seriescontain information grouped by fields defined ingroup_by. Only grouping byqueueis allowed.
The data (seeabove) are wrapped invaluesobject,
and accompanied by the values of attributes that were used for grouping.
Series
group_by
queue
values
AttributeTypeDescriptionqueueURLQueue of billed pages or documentsbegin_datedateStart date of the documents with billed items within the groupend_datedateFinal date of the documents with billed items within the groupvaluesobjectContains the data oftotalslist grouped by queue and date.
totals


## Organization group

Example organization group object

```
{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu","features":null,"usage":{}}
```

{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu","features":null,"usage":{}}
Organization group object represents coupling among organizations.
AttributeTypeDescriptionRead-onlyidintegerId of the organization groupnamestringName of the organization groupis_trialboolProperty indicates whether this license is a trial licensetrueis_productionboolProperty indicates whether this licence is a production licencetruedeployment_locationstringDeployment location identifiertruefeaturesobjectEnabled features (for internal use only)trueusageobjectEnabled priced features (for internal use only)truemodified_byURLURL of the last modifiertruemodified_atdatetimeDate of the last modificationtrue

### List all organization groups

List all organization groups.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu","features":null,"usage":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu","features":null,"usage":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
GET /v1/organization_groups
GET /v1/organization_groups
Retrieve all organization group objects.

#### Response

Status:200
200
Returnspaginatedresponse with a list oforganization groupobjects. Typically, there would only be one result.

### Retrieve an organization group

Get organization group object42
42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42'

```
{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu",...}
```

{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu",...}
GET /v1/organization_groups/{id}
GET /v1/organization_groups/{id}
Get an organization group object.

#### Response

Status:200
200
Returnsorganization groupobject.

### Create a new organization group

Create a new organization group

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organization_groups'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organization_groups'

```
{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu",...}
```

{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu",...}
POST /v1/organization_groups
POST /v1/organization_groups
Create a neworganization groupobject.

#### Response

Status:201
201
Returns the createdorganization groupobject.

### Managing memberships

The following endpoints provide read-only views for users with theorganization_group_adminrole  for managing memberships. The returned object views have a selected subset of their attributes. The URL attributes point to the membership objects instead of the full views.
organization_group_admin
organization_group_admin

#### Membership User

AttributeTypeDescriptionidintegerId of the userurlURLMembership URL of the useremailstringEmail of the userusernamestringUsername of a userorganizationURLRelatedorganization

#### Retrieve a User

Get user123456from organization group42
123456
42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/users/123456'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/users/123456'

```
{"id":123456,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/users/123456","email":"john-doe@east-west-trading.com","username":"JohnDoe","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321"}
```

{"id":123456,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/users/123456","email":"john-doe@east-west-trading.com","username":"JohnDoe","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321"}
GET /v1/organization_groups/{organization_group_id}/users/{user_id}
GET /v1/organization_groups/{organization_group_id}/users/{user_id}
Get user for an organization group object.
Status:200
200
Retrieve a singleorganization groupuser.

#### List all Users in an Organization group

Get users from organization group42
42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/users'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/users'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":123456,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/users/123456","email":"john-doe@east-west-trading.com","username":"JohnDoe","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321"},{...}]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":123456,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/users/123456","email":"john-doe@east-west-trading.com","username":"JohnDoe","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321"},{...}]}
GET /v1/organization_groups/{id}/users
GET /v1/organization_groups/{id}/users
Get users for an organization group object.
Status:200
200
Retrieve allorganization groupusers.

#### Membership Organization

AttributeTypeDescriptionidintegerId of the organizationurlURLMembership URL of the organizationnamestringName of the organization (not visible in UI)

#### Retrieve an Organization

Get organization321from organization group42
321
42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321'

```
{"id":321,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","name":"East West Trading Co"}
```

{"id":321,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","name":"East West Trading Co"}
GET /v1/organization_groups/{organization_group_id}/organizations/{organization_id}
GET /v1/organization_groups/{organization_group_id}/organizations/{organization_id}
Get organization for an organization group object.
Status:200
200
Retrieve a singleorganization grouporganization.

#### List all Organizations in an Organization group

Get organizations from organization group42
42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/organizations'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/organizations'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":321,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","name":"East West Trading Co"},{...}]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":321,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","name":"East West Trading Co"},{...}]}
GET /v1/organization_groups/{id}/organizations
GET /v1/organization_groups/{id}/organizations
Get organizations for an organization group object.
Status:200
200
Retrieve allorganization grouporganizations.

#### Membership workspace

AttributeTypeDescriptionidintegerId of the workspaceurlURLMembership URL of the workspacenamestringName of the workspaceorganizationURLMembership URL of the organizationqueueslist[URL]Membership URLs of the queues

#### Retrieve a Workspace

Get workspace345from organization group42
345
42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/345'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/345'

```
{"id":345,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/345","name":"East West Trading Co","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/123","queues":["https://<example>.rossum.app/api/v1/organization_groups/42/queues/1","https://<example>.rossum.app/api/v1/organization_groups/42/queues/2"]}
```

{"id":345,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/345","name":"East West Trading Co","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/123","queues":["https://<example>.rossum.app/api/v1/organization_groups/42/queues/1","https://<example>.rossum.app/api/v1/organization_groups/42/queues/2"]}
GET /v1/organization_groups/{organization_group_id}/workspaces/{workspace_id}
GET /v1/organization_groups/{organization_group_id}/workspaces/{workspace_id}
Get workspace for an organization group object.
Status:200
200
Retrieve a singleorganization groupworkspace.

#### List all Workspaces in an Organization group

Get workspaces from organization group42
42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/workspaces'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/workspaces'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":345,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/345","name":"East West Trading Co","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/123","queues":["https://<example>.rossum.app/api/v1/organization_groups/42/queues/1","https://<example>.rossum.app/api/v1/organization_groups/42/queues/2"]},{...}]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":345,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/345","name":"East West Trading Co","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/123","queues":["https://<example>.rossum.app/api/v1/organization_groups/42/queues/1","https://<example>.rossum.app/api/v1/organization_groups/42/queues/2"]},{...}]}
GET /v1/organization_groups/{id}/workspaces
GET /v1/organization_groups/{id}/workspaces
Get workspaces for an organization group object.
Supported filters:organization
organization
For additional info please refer tofilters and ordering.
Status:200
200
Retrieve allorganization groupworkspaces.

#### Membership Queue

AttributeTypeDescriptionidintegerId of the queueurlURLMembership URL of the queuenamestringName of the queueorganizationURLMembership URL of theorganizationworkspaceURLMembership URL of the workspace

#### Retrieve a Queue

Get queue654from organization group42
654
42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/queues/654'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/queues/654'

```
{"id":654,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/queues/654","name":"Received invoices","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","workspace":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/12"}
```

{"id":654,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/queues/654","name":"Received invoices","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","workspace":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/12"}
GET /v1/organization_groups/{organization_group_id}/queues/{queue_id}
GET /v1/organization_groups/{organization_group_id}/queues/{queue_id}
Get queue for an organization group object.
Status:200
200
Retrieve a singleorganization groupqueue.

#### List all Queues in an Organization group

Get queues from organization group42
42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/queues'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/queues'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":654,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/queues/654","name":"Received invoices","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","workspace":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/12"},{...}]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":654,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/queues/654","name":"Received invoices","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","workspace":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/12"},{...}]}
GET /v1/organization_groups/{id}/queues
GET /v1/organization_groups/{id}/queues
Get queues for an organization group object.
Supported filters:organization
organization
For additional info please refer tofilters and ordering.
Status:200
200
Retrieve allorganization groupqueues.

### Billing for organization group


#### Billing stats for organization group

Download billing stats report (Sep 1, 2021 - August 31, 2022).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-09-01", "end_date": "2022-08-31", "queues": [
      "https://<example>.rossum.app/api/v1/organization_groups/42/queues/8199", null]}, "group_by": ["queue"]}'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_stats'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-09-01", "end_date": "2022-08-31", "queues": [
      "https://<example>.rossum.app/api/v1/organization_groups/42/queues/8199", null]}, "group_by": ["queue"]}'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_stats'
POST /v1/organization_groups/{id}/billing_stats
POST /v1/organization_groups/{id}/billing_stats
AttributeTypeDescriptionfilterobjectFilters used for the computation of billed items counts (seeorganization group billing stats filtersbelow)group_bylist[string]List of attributes by which theresultsare to be grouped. Only a single value is supported. Possible values:organization,queue,monthandweekorder_bylist[string]List of attributes by which theresultsare to be ordered. Possible values:billable_pages,billable_documents,non_billable_pages,non_billable_pages
results
organization
queue
month
week
results
billable_pages
billable_documents
non_billable_pages
non_billable_pages
AttributeTypeDescriptionqueueslist[URL]Membership URL of the queues (ornullfor historically deleted queues) to be counted in the report (see the note below)organizationslist[URL]Membership URL of the organizations to be counted in the reportbegin_datedatetimeFilter billed items that was issuedsincethe specified date (including the specified date) to be counted to the report.end_datedatetimeFilter billed items that was issuedup tothe specified date (including the specified date) to be counted to the report.
null
Additionally there are some limitations with regards to the filter.queues and groupings that can be used together:
- filter.queuescan only be used whenfilter.organizationscontains a single organization
filter.queuescan only be used whenfilter.organizationscontains a single organization
filter.queues
filter.organizations
- filter.queuescannot be used forgroup_by=organization
filter.queuescannot be used forgroup_by=organization
filter.queues
group_by=organization
Status:200
200

```
{"pagination":{"next":null,"previous":null,"total":12,"total_pages":1},"results":[{"begin_date":"2021-10-01","end_date":"2021-10-31","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/406","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","queue":"https://<example>.rossum.app/api/v1/organization_groups/42/queues/8199","values":{"billable_documents":32,"billable_pages":27,"non_billable_documents":0,"non_billable_pages":0}},{"begin_date":"2021-10-01","end_date":"2021-10-31","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/406","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","queue":null,"values":{"billable_documents":147,"billable_pages":59,"non_billable_documents":0,"non_billable_pages":0}},...],"totals":{"billable_documents":21288,"billable_pages":30204,"non_billable_documents":81,"non_billable_pages":5649},"updated_at":"2022-09-01"}
```

{"pagination":{"next":null,"previous":null,"total":12,"total_pages":1},"results":[{"begin_date":"2021-10-01","end_date":"2021-10-31","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/406","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","queue":"https://<example>.rossum.app/api/v1/organization_groups/42/queues/8199","values":{"billable_documents":32,"billable_pages":27,"non_billable_documents":0,"non_billable_pages":0}},{"begin_date":"2021-10-01","end_date":"2021-10-31","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/406","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","queue":null,"values":{"billable_documents":147,"billable_pages":59,"non_billable_documents":0,"non_billable_pages":0}},...],"totals":{"billable_documents":21288,"billable_pages":30204,"non_billable_documents":81,"non_billable_pages":5649},"updated_at":"2022-09-01"}
For more details seebilling stats for organization.

#### Billing history for organization group

Retrieve billing history report.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_history'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_history'
GET /v1/organization_groups/{id}/billing_history
GET /v1/organization_groups/{id}/billing_history
Retrieve billing history with entries corresponding to individual contracted periods. The valuepuchased_documentsorpurchased_pagesdefine the period billing unit.
puchased_documents
purchased_pages
Status:200
200

```
{"pagination":{"next":null,"previous":null,"total":2,"total_pages":1},"results":[{"begin_date":"2021-01-01","end_date":"2022-12-31","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","values":{"billable_documents":0,"non_billable_documents":0,"billable_pages":34735,"non_billable_pages":100,"is_current":true,"purchased_documents":0,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}},{"begin_date":"2020-01-01","end_date":"2021-12-31","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","values":{"billable_documents":10209,"non_billable_documents":200,"billable_pages":0,"non_billable_pages":0,"is_current":false,"purchased_documents":111,"purchased_pages":0,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}}],"totals":{"billable_documents":10209,"non_billable_documents":200,"billable_pages":34735,"non_billable_pages":100,"purchased_documents":111,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0},"updated_at":"2022-09-01"}
```

{"pagination":{"next":null,"previous":null,"total":2,"total_pages":1},"results":[{"begin_date":"2021-01-01","end_date":"2022-12-31","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","values":{"billable_documents":0,"non_billable_documents":0,"billable_pages":34735,"non_billable_pages":100,"is_current":true,"purchased_documents":0,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}},{"begin_date":"2020-01-01","end_date":"2021-12-31","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","values":{"billable_documents":10209,"non_billable_documents":200,"billable_pages":0,"non_billable_pages":0,"is_current":false,"purchased_documents":111,"purchased_pages":0,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}}],"totals":{"billable_documents":10209,"non_billable_documents":200,"billable_pages":34735,"non_billable_pages":100,"purchased_documents":111,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0},"updated_at":"2022-09-01"}

#### Billing stats export for organization group

Download billing stats CSV report (Sep 1, 2021 - August 31, 2022).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-10-01", "end_date": "2022-09-31"}, "group_by": ["month"]}'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_stats/export'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-10-01", "end_date": "2022-09-31"}, "group_by": ["month"]}'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_stats/export'
POST /v1/organization_groups/{id}/billing_stats/export
POST /v1/organization_groups/{id}/billing_stats/export
Download the data provided by thebilling stats response resourcein a CSV output.
Status:200
200

```
begin_date,end_date,billable_pages,non_billable_pages,billable_documents,non_billable_documents
2021-10-01,2021-10-31,27,0,32,0
2021-11-01,2021-11-30,159,0,147,9
2021-12-01,2021-12-31,41,0,20,0
2022-01-01,2022-01-31,143,0,113,0
2022-02-01,2022-02-28,275,0,134,0
2022-03-01,2022-03-31,57,0,44,0
2022-04-01,2022-04-30,145,0,83,1
2022-05-01,2022-05-31,53,0,17,0
2022-06-01,2022-06-30,26837,5586,18061,18
2022-07-01,2022-07-31,3033,63,3014,64
2022-08-01,2022-08-31,347,0,101,0
2022-09-01,2022-09-31,117,0,28,4
```

begin_date,end_date,billable_pages,non_billable_pages,billable_documents,non_billable_documents
2021-10-01,2021-10-31,27,0,32,0
2021-11-01,2021-11-30,159,0,147,9
2021-12-01,2021-12-31,41,0,20,0
2022-01-01,2022-01-31,143,0,113,0
2022-02-01,2022-02-28,275,0,134,0
2022-03-01,2022-03-31,57,0,44,0
2022-04-01,2022-04-30,145,0,83,1
2022-05-01,2022-05-31,53,0,17,0
2022-06-01,2022-06-30,26837,5586,18061,18
2022-07-01,2022-07-31,3033,63,3014,64
2022-08-01,2022-08-31,347,0,101,0
2022-09-01,2022-09-31,117,0,28,4

#### Billing history export for organization group

Download billing history CSV report.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_history/export'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_history/export'
GET /v1/organization_groups/{id}/billing_history/export
GET /v1/organization_groups/{id}/billing_history/export
Download the data provided by thebilling history response resourcein a CSV output.
Status:200
200

```
begin_date,end_date,purchased_pages,billable_pages,non_billable_pages,purchased_documents,billable_documents,non_billable_documents,extracted_pages_with_learning,extracted_pages_without_learning,split_pages_with_learning,split_pages_without_learning,extracted_documents_with_learning,extracted_documents_without_learning,split_documents_with_learning,split_documents_without_learning,ocr_only_pages,ocr_only_documents,purchased_extracted_pages_with_learning,purchased_extracted_pages_without_learning,purchased_split_pages_with_learning,purchased_split_pages_without_learning,purchased_extracted_documents_with_learning,purchased_extracted_documents_without_learning,purchased_split_documents_with_learning,purchased_split_documents_without_learning,purchased_ocr_only_pages,purchased_ocr_only_documents
2021-01-01,2022-12-31,555,34735,100,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2020-01-01,2021-12-31,0,0,0,111,10209,123,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
```

begin_date,end_date,purchased_pages,billable_pages,non_billable_pages,purchased_documents,billable_documents,non_billable_documents,extracted_pages_with_learning,extracted_pages_without_learning,split_pages_with_learning,split_pages_without_learning,extracted_documents_with_learning,extracted_documents_without_learning,split_documents_with_learning,split_documents_without_learning,ocr_only_pages,ocr_only_documents,purchased_extracted_pages_with_learning,purchased_extracted_pages_without_learning,purchased_split_pages_with_learning,purchased_split_pages_without_learning,purchased_extracted_documents_with_learning,purchased_extracted_documents_without_learning,purchased_split_documents_with_learning,purchased_split_documents_without_learning,purchased_ocr_only_pages,purchased_ocr_only_documents
2021-01-01,2022-12-31,555,34735,100,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2020-01-01,2021-12-31,0,0,0,111,10209,123,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0


## Page

Example page object

```
{"id":558598,"annotation":"https://<example>.rossum.app/api/v1/annotations/314528","number":1,"rotation_deg":0,"mime_type":"image/png","s3_name":"4b66305775c029cb0cfa80fd0ebb2da6","url":"https://<example>.rossum.app/api/v1/pages/558598","content":"https://<example>.rossum.app/api/v1/pages/558598/content","metadata":{},"width":1440,"height":668}
```

{"id":558598,"annotation":"https://<example>.rossum.app/api/v1/annotations/314528","number":1,"rotation_deg":0,"mime_type":"image/png","s3_name":"4b66305775c029cb0cfa80fd0ebb2da6","url":"https://<example>.rossum.app/api/v1/pages/558598","content":"https://<example>.rossum.app/api/v1/pages/558598/content","metadata":{},"width":1440,"height":668}
A page object contains information about one page of the annotation (we render
pages separately for every annotation, but this will change in the future).
Page objects are created automatically during document import and cannot be
created through the API, you need to use queueuploadendpoint. Pages cannot be deleted directly -- they are deleted on parent annotation delete.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the pagetrueurlURLURL of the page.trueannotationURLAnnotation that page belongs to.numberintegerPage index, first page has index 1.rotation_degintegerPage rotation.mime_typestringMIME type of the page (image/png).trues3_namestringInternaltruecontentURLLink to the page raw content (e.g. pdf file).metadataobject{}Client data.widthintegernullPage width (for internal purposes only)trueheightintegernullPage height (for internal purposes only)true
image/png
{}

### List all pages

List all pages

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/pages'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/pages'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":558598,"annotation":"https://<example>.rossum.app/api/v1/annotations/314528","number":1,"rotation_deg":0,"mime_type":"image/png","s3_name":"7eb0dcc0faa8868b55fb425d21cc60dd","url":"https://<example>.rossum.app/api/v1/pages/558598","content":"https://<example>.rossum.app/api/v1/pages/558598/content","metadata":{},"width":null,"height":null}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":558598,"annotation":"https://<example>.rossum.app/api/v1/annotations/314528","number":1,"rotation_deg":0,"mime_type":"image/png","s3_name":"7eb0dcc0faa8868b55fb425d21cc60dd","url":"https://<example>.rossum.app/api/v1/pages/558598","content":"https://<example>.rossum.app/api/v1/pages/558598/content","metadata":{},"width":null,"height":null}]}
GET /v1/pages
GET /v1/pages
Retrieve all page objects.
Supported filters:id,annotation,number
id
annotation
number
Supported ordering:id,number,s3_name
id
number
s3_name
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofpageobjects.

### Retrieve a page

Get page object558598
558598

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/pages/558598'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/pages/558598'

```
{"id":558598,"annotation":"https://<example>.rossum.app/api/v1/annotations/314528","number":1,"rotation_deg":0,"mime_type":"image/png","s3_name":"7eb0dcc0faa8868b55fb425d21cc60dd","url":"https://<example>.rossum.app/api/v1/pages/558598","content":"https://<example>.rossum.app/api/v1/pages/558598/content","metadata":{}}
```

{"id":558598,"annotation":"https://<example>.rossum.app/api/v1/annotations/314528","number":1,"rotation_deg":0,"mime_type":"image/png","s3_name":"7eb0dcc0faa8868b55fb425d21cc60dd","url":"https://<example>.rossum.app/api/v1/pages/558598","content":"https://<example>.rossum.app/api/v1/pages/558598/content","metadata":{}}
GET /v1/pages/{id}
GET /v1/pages/{id}
Get a page object.


## Question

Example question object

```
{"uuid":"9e87fcf2-f571-4691-8850-77f813d6861a","text":"How satisfied are you?","answer_type":"scale"}
```

{"uuid":"9e87fcf2-f571-4691-8850-77f813d6861a","text":"How satisfied are you?","answer_type":"scale"}
A Question object represents a collection of questions related to asurvey.
AttributeTypeDescriptionuuidstringUUID of the questionurlURLURL of the questiontextstringText body of the questionanswer_typeenumDetermines the shape of the answer. Possible values: seeanswer type

### List all questions

List all questions

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/questions'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/questions'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a",...}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a",...}]}
GET /v1/questions
GET /v1/questions
Retrieve all question objects.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofquestionobjects.

### Retrieve a question

Get question object9e87fcf2-f571-4691-8850-77f813d6861a
9e87fcf2-f571-4691-8850-77f813d6861a

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a'

```
{"url":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a",...}
```

{"url":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a",...}
GET /v1/questions/{uuid}
GET /v1/questions/{uuid}
Get a question object.

#### Response

Status:200
200
Returnsquestionobject.


## Queue

Example queue object

```
{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","connector":null,"webhooks":[],"hooks":[],"schema":"https://<example>.rossum.app/api/v1/schemas/31336","inbox":"https://<example>.rossum.app/api/v1/inboxes/1229","users":["https://<example>.rossum.app/api/v1/users/10775"],"session_timeout":"01:00:00","rir_url":"https://all.rir.rossum.ai","rir_params":null,"dedicated_engine":null,"generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876","engine":null,"counts":{"importing":0,"split":0,"failed_import":0,"to_review":2,"reviewing":0,"confirmed":0,"exporting":0,"postponed":0,"failed_export":0,"exported":0,"deleted":0,"purged":0,"rejected":0},"default_score_threshold":0.8,"automation_enabled":false,"automation_level":"never","locale":"en_US","metadata":{},"use_confirmed_state":false,"document_lifetime":"01:00:00","delete_after":null,"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z","settings":{"columns":[{"schema_id":"tags"}],"hide_export_button":true,"automation":{"automate_duplicates":true,"automate_suggested_edit":false},"rejection_config":{"enabled":true},"dashboard_customization":{"all_documents":false,"confirmed":true,"deleted":true,"exported":true,"postponed":true,"rejected":true,"to_review":true},"email_notifications":{"recipient":{"email":"john.doe@company.com","name":"John Doe"},"unprocessable_attachments":false,"email_with_no_attachments":true,"postponed_annotations":false,"deleted_annotations":false},"workflows":{"enabled":false}},"workflows":[{"url":"https://<example>.rossum.app/api/v1/workflows/1","priority":2}]}
```

{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","connector":null,"webhooks":[],"hooks":[],"schema":"https://<example>.rossum.app/api/v1/schemas/31336","inbox":"https://<example>.rossum.app/api/v1/inboxes/1229","users":["https://<example>.rossum.app/api/v1/users/10775"],"session_timeout":"01:00:00","rir_url":"https://all.rir.rossum.ai","rir_params":null,"dedicated_engine":null,"generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876","engine":null,"counts":{"importing":0,"split":0,"failed_import":0,"to_review":2,"reviewing":0,"confirmed":0,"exporting":0,"postponed":0,"failed_export":0,"exported":0,"deleted":0,"purged":0,"rejected":0},"default_score_threshold":0.8,"automation_enabled":false,"automation_level":"never","locale":"en_US","metadata":{},"use_confirmed_state":false,"document_lifetime":"01:00:00","delete_after":null,"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z","settings":{"columns":[{"schema_id":"tags"}],"hide_export_button":true,"automation":{"automate_duplicates":true,"automate_suggested_edit":false},"rejection_config":{"enabled":true},"dashboard_customization":{"all_documents":false,"confirmed":true,"deleted":true,"exported":true,"postponed":true,"rejected":true,"to_review":true},"email_notifications":{"recipient":{"email":"john.doe@company.com","name":"John Doe"},"unprocessable_attachments":false,"email_with_no_attachments":true,"postponed_annotations":false,"deleted_annotations":false},"workflows":{"enabled":false}},"workflows":[{"url":"https://<example>.rossum.app/api/v1/workflows/1","priority":2}]}
A queue object represents a basic organization unit of annotations. Annotations
are imported to a queue either through a REST APIupload endpointor by sending an email to a relatedinbox. Export is also performed on a
queue usingexportendpoint.
Queue also specifies aschemafor annotations and aconnector.
Annotators and viewers only see queues they are assigned to.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the queuetruenamestringName of the queue (max. 255 characters)urlURLURL of the queuetrueworkspaceURLWorkspace in which the queue should be placed (it can be set tonull, but bare in mind that it will make the queue invisible in the Rossum UI and it may cause some unexpected consequences)connectorURLnullConnector associated with the queuewebhookslist[URL][](Deprecated) Webhooks associated with the queue (serves as an alias forhooksattribute)hooksURLlist[URL][]Hooks associated with the queueschemaURLSchema which will be applied to annotations in this queueinboxURLnullInbox for import to this queueuserslist[URL][]Users associated with this queuesession_timeouttimedelta1 hourTime before annotation will be returned fromrevievingstatus toto_review(timeout is evaluated every 10 minutes)rir_urlURLnull(Deprecated) Usegeneric_engineordedicated_engineto set AI Core Engine.generic_engineURLnullGeneric engine used for processing documents uploaded to this queue. Ifgeneric_engineis setdedicated_enginemust benull. If both engines arenull, a default generic one gets set.dedicated_engineURLnullDedicated engine used for processing documents uploaded to this queue. Ifdedicated_engineis setgeneric_enginemust benull.rir_paramsstringnullURL parameters to be passed to the AI Core Engine, see belowcountsobjectCount of annotations perstatustruedefault_score_thresholdfloat [0;1]0.8Threshold used to automatically validate field content based onAI confidence scores.automation_enabledboolfalseToggle for switching automation on/offautomation_levelstringneverSet level of automation, seeAutomation level.localestringen_GBTypical originating region of documents processed in this queue specified in the locale format, see below. Ifautooption is chosen, the locale will be detected automatically if the organization group has access to Aurora engine. Otherwise, default option (en_GB) will be used.metadataobject{}Client data.use_confirmed_stateboolfalseAffects exporting: whentrue,confirmendpoint transitions annotation toconfirmedstatus instead toexporting.settingsobject{}Queue UI settingsdocument_lifetimedurationnullData retention period -- annotations will be automatically purged this time after their creation. The format of the value is '[DD] [HH:[MM:]]ss[.uuuuuu]', e.g. 90 days retention can be set as '90 00:00:00'. Please keep in mind that purging documents in Rossum can limit its learning capabilities. This is a priced feature and has no effect unless enabled.delete_afterdatetimenullFor internal use only (When a queue is marked for its deletion it will be done after this date)truestatusstringactiveCurrent status of the queue, seeQueue statustruemodified_byURLnullLast modifier.truemodified_atdatetimenullTime of last modification.trueworkflowslist[object][][BETA]Workflows set for the queue. Read more about the objectshere
null
null
[]
hooks
[]
null
[]
revieving
to_review
null
generic_engine
dedicated_engine
null
generic_engine
dedicated_engine
null
null
null
dedicated_engine
generic_engine
null
null
false
auto
en_GB
{}
false
true
confirmed
exporting
{}
null
null
active
null
null
[]
rir_url
agenda
rir_params
generic_engine
dedicated_engine
rir_url
generic_engine
dedicated_engine
default_score_threshold
default_score_threshold
More specific AI Core Engine parameters influencing the extraction may be set usingrir_paramsfield.
So far, these parameters are publicly available:
rir_params
- effective_page_count(int): Limits the extraction to the firsteffective_page_countpages of the document.Useful to prevent data extraction from additional pages of unrelated, but included documents.Default: 32 (pages to be extracted from a document).
effective_page_count(int): Limits the extraction to the firsteffective_page_countpages of the document.
effective_page_count
effective_page_count
- Useful to prevent data extraction from additional pages of unrelated, but included documents.
- Default: 32 (pages to be extracted from a document).
- tables(boolean): Allows disabling line item data extraction.Useful to speed up data extraction when line item details are not required, especially on long documents with large tables.Default: true (line items are being extracted).
tables(boolean): Allows disabling line item data extraction.
tables
- Useful to speed up data extraction when line item details are not required, especially on long documents with large tables.
- Default: true (line items are being extracted).
Thelocalefield is a hint for theAI Engineon how to resolve some ambiguous cases during data extraction, concerning e.g. date formats or decimal separators that may depend on the locale.  For example, in US the typical date format is mm/dd/yyyy whilst in Europe it is dd.mm.yyyy. A date such as "12. 6. 2018" will be extracted as Jun 12 when locale isen_GB, while the same date will be extracted as Dec 6 when locale isen_US.
locale
en_GB
en_US
For backward compatibility,webhooksattribute is an alias ofhooks. If both attributes are specified,webhooksoverrideshooks. For new integrations, do not specifywebhooksattribute.
webhooks
hooks
webhooks
hooks
webhooks

#### Automation level

With queue attributeautomation_levelyou can set at which circumstances
should be annotation auto-exported after the AI-based data extraction, without
validation in the UI (skipping theto_reviewandreviewingstate).
automation_level
to_review
reviewing
Attribute can have following options:
Automation levelDescriptionalwaysAuto-export all documents with no validation errors. When there is an error triggered for a non-required field, such values are deleted and export is re-tried.confidentAuto-export documents with at least onevalidation sourceand no validation errors.neverAnnotation is not automatically exported and must be validated in UI manually.

#### Queue status

Queue statusDescriptionactiveThis is the default status. Queue is usable.deletion_requestedQueue is marked for deletion (by callingDELETE /v1/queues/<id>). Will be asynchronously deleted afterdelete_after.deletion_in_progressQueue is currently being deleted. When a queue has this status some raise conditions may occur as the related objects are being gradually deleted.deletion_failedSomething wrong happened in the process of queue deletion. The queue may be in an inconsistent state.
DELETE /v1/queues/<id>
delete_after
Please note, that document import (via upload as well as email) is disabled while the queue status is one ofdeletion_requested,deletion_in_progress,deletion_failed.
deletion_requested
deletion_in_progress
deletion_failed

#### Settings attribute

AttributeTypeDefaultDescriptionRead-onlycolumnslist[object][](Deprecated, useannotation_list_tableinstead) List that contains schema ids to be shown on a dashboard.hide_export_buttonbooltrueToggle to uncover "Export" button on dashboard (useful whenqueue.use_confirmed_state = true), which allows manual export of annotations inconfirmedstatus.autopilotobjectnullAutopilot configuration describing which fields can be confirmed automatically.accepted_mime_typeslist[str][]List ofMIME typeswhich can be uploaded to the queue. This can contain wildcards such asimage/*or exact type likeapplication/pdf.asynchronous_exportbooltrue(Deprecated) Always set totrue. Theconfirmendpoint returns immediately and hooks' and connector'ssaveendpoint is called asynchronously later on. This value is used only when queue does not have a connector.automationobject{}Queue automation settings, seeautomation settingsrejection_configobject{default}Queue rejection settings, seerejection settingssuggested_recipients_sourceslist[object][{default}]Queue suggested email recipients settings, seesuggested recipients settingssuggested_editstrdisableAllow to split document (semi-)automatically. Allowed values are:suggestanddisable.dashboard_customizationobject{default}Dashboard customization settings, seedashboard customization settingsemail_notificationsobject{default}Queue email notifications settings, seeemail notifications settingsworkflowsobject{default}[BETA]Please note that this can be modified only when the workflows addon is enabled (read more detailshere).annotation_list_tableobject{}Configuration of annotation dashboard columnsupload_valueslist[object][]Configuration of values to be specified duringupload(seedefinition of the object)ui_upload_enabledbooltrueFlag for enabling upload for particular queue in Rossum UI.falseui_on_edit_confirmstrvalidate_firstChanges edit screen confirm button behavior. Allowed values are:annotation_list,edit_next,validate_first.ui_validation_screen_enabledbooltrueFlag for enabling validation screen for a particular queue in Rossum UI. If disabled, opening of a document will trigger a redirect to an edit screen.falseui_edit_valueslist[object][]Configuration of values to be specified duringedit_pages(seedefinition of the object)
annotation_list_table
true
queue.use_confirmed_state = true
confirmed
null
image/*
application/pdf
true
true
save
{}
disable
suggest
disable
{}
[]
true
validate_first
annotation_list
edit_next
validate_first
true
[]

#### Automation settings

AttributeTypeDefaultDescriptionRead-onlyautomate_duplicatesbooltrueWhen set totrue, automation will be enabled for documents that have a duplicates. Disabled if parameter isfalse.falseautomate_suggested_editboolfalseWhen set totrue, automation will be enabled for annotations containingsuggested edits. Disabled if parameter isfalse.false
true
true
false
false
false
true
false
false

#### Rejection settings

AttributeTypeDefaultDescriptionRead-onlyenabledbooltrueDashboardRejectedis visible in application when enabled is set totrue.false
true
Rejected
true
false

#### Suggested recipients sources settings

AttributeTypeDefaultDescriptionRead-onlysourcestringemail_headerIndicates source of the suggested recipients email address, seepossible sources.falseschema_idstringUsed for finding appropriate datapoint value in annotation data (necessary only for vendor_database and extracted_value sources).false
false
false

#### Suggested recipients possible sources

SourceDescriptionemail_headerEmail is taken from the sender in header of the email. See email onannotation.extracted_valueEmail is extracted from annotation data - schema_id is used to find requested value.vendor_databaseEmail is extracted from annotation data - schema_id is used to find requested value. Value is filled by vendor matching connector.queue_mailing_history[BETA]Emails are taken from all the recipient inside all the emails send inside the email's queue. See email onannotation.organization_users*[BETA]Emails are taken from the users of related organization
- List of the organization users is filtered based on the role of an user that is requesting the data

#### Dashboard customization settings

AttributeTypeDefaultDescriptionall_documentsstringfalseWhen set totrue, all UI tabs are merged into one, so the documents with different statuses are mixes in one tab instead of having its own one.confirmedbooltrueWhen set totrue, UI tab forconfirmeddocuments will be shown. Relates to the queue settings attributeuse_confirmed_stateis set to true.deletedbooltrueWhen set totrue, UI tab for documents indeletedstate will be shown.exportedbooltrueWhen set totrue, UI tab for documents inexportedstate will be shown.postponedbooltrueWhen set totrue, UI tab for documents inpostponedstate will be shown.rejectedbooltrueWhen set totrue, UI tab for documents inrejectedstate will be shown.to_reviewbooltrueWhen set totrue, UI tab for documents into_reviewstate will be shown.
true
true
confirmed
use_confirmed_state
true
deleted
true
exported
true
postponed
true
rejected
true
to_review

#### Email notifications settings

AttributeTypeDefaultDescriptionRead-onlyrecipientobjectNoneInformation about email address to send notifications to (e.g. about failed import). It contains keysemailandname.falseunprocessable_attachmentsboolfalseWhether return back unprocessable attachments (e.g. MS Word docx) or just silently ignore them. When true,minimum image sizerequirement does not apply.falsepostponed_annotationsboolfalseWhether to send notification when annotation is postponed.falsedeleted_annotationsboolfalseWhether to send notification when annotation is deleted.falseemail_with_no_attachmentsbooltrueWhether to send notification when no processable documents were found.false
None
email
name
false
false
false
false
false
false
false
true
false
AttributeTypeDefaultRead-onlyrecipientobjectNonefalseunprocessable_attachmentsboolFalsefalsepostponed_annotationsboolFalsefalsedeleted_annotationsboolFalsefalseemail_with_no_attachmentsboolTruefalse
false
false
false
false
false

#### Workflows settings

AttributeTypeDefaultDescriptionRead-onlyenabledboolfalseDashboardWorkflowsis visible in application when enabled is set totrue. Also enables the workflow automation.falsebypass_workflows_allowedboolfalseWhether to allow toconfirmannotation with optionskip_workflows=true
false
Workflows
true
false
false
skip_workflows=true

#### Annotation list table configuration

AttributeTypeDefaultDescriptionRead-onlycolumnslist[object][]Configuration of columns on annotation dashboard (seedefinition of the object)false
list[object]
[]
false

#### Annotation list table column configuration

AttributeTypeDescriptionvisibleboolColumn is visible on the dashboardwidthfloatWidth of the columncolumn_typeenumType of the field (meta- annotation meta field,schema- annotation content field)schema_idstringschema_idof the extracted field (only forcolumn_type=schema)data_typeenumData type of the extracted field (only forcolumn_type=schema). Allowed values aredate,number,string,booleanmeta_typeenumMeta column type (only forcolumn_type=meta). Allowed values can be found inmeta_fieldtable(+ additionallydetails)
meta
schema
schema_id
column_type=schema
column_type=schema
date
number
string
boolean
column_type=meta
meta_field
details

#### Upload values configuration

Value obtained from the user in the upload dialog may be passed as an upload value or in an annotationmetadatafield. SeeUploadfor details.
AttributeTypeDescriptionRequiredDefaultidstringID of the valueyestypestringType of the value:valuesormetadata— specify how to pass the valuenovaluesdata_typestringData type of the value:enumorstringnostringlabelstringLabel to be used in UIyesenum_optionslist[object]List of objects withvalueandlabelfields. Only allowed forenumtype.nonullrequiredboolWhether the value is required to be set during uploadnofalse
values
metadata
values
enum
string
string
value
label
enum
false

#### UI Edit values configuration

Value obtained from the user in the edit screen may be passed as an edit value. SeeEdit pagesandSuggested Editfor details.
AttributeTypeDescriptionRequiredDefaultidstringID of the valueyeslabelstringLabel to be used in UIyesdata_typestringType of the value:enumorstringyesenum_optionslist[object]List of objects withvalueandlabelfields. Only allowed forenumdata_type.nonullrequiredboolWhether the value is required to be set during editnofalse
enum
string
value
label
enum
false
Schema Datapoint descriptiondescribes how edit values are used to initialize datapoint values.

#### Queue workflows

AttributeTypeDescriptionRead-onlyurlurlUrl of the workflow objectfalsepriorityintegerPriority of the linked workflow. Designate the order of their evaluation (lower number means it's evaluated sooner)false
false
false

### Import a document

Upload file using a form (multipart/form-data)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
Upload file in a request body

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
Upload file in a request body (UTF-8 filename must be URL encoded)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H"Content-Disposition: attachment; filename*=utf-8''document%20%F0%9F%8E%81.pdf"--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H"Content-Disposition: attachment; filename*=utf-8''document%20%F0%9F%8E%81.pdf"--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
Upload file in a request body with a filename in URL (UTF-8 filename must be URL encoded)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload/document%20%F0%9F%8E%81.pdf'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload/document%20%F0%9F%8E%81.pdf'
Upload multiple files using multipart/form-data

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document1.pdf-Fcontent=@document2.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document1.pdf-Fcontent=@document2.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
Upload file using basic authentication

```
curl-u'east-west-trading-co@<example>.rossum.app:secret'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

curl-u'east-west-trading-co@<example>.rossum.app:secret'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
Upload file with additional field values and metadata

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\-Fvalues='{"upload:organization_unit":"Sales"}'\-Fmetadata='{"project":"Market ABC"}'\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\-Fvalues='{"upload:organization_unit":"Sales"}'\-Fmetadata='{"project":"Market ABC"}'\'https://<example>.rossum.app/api/v1/queues/8236/upload'
POST /v1/queues/{id}/upload
POST /v1/queues/{id}/upload
POST /v1/queues/{id}/upload/{filename}
POST /v1/queues/{id}/upload/{filename}
Uploads a document to the queue (starting in theimporting state). This
creates adocumentobject and an emptyannotationobject.
The file can be sent as a part of multipart/form-data or, alternatively, in the
request body. Multiple files upload is supported, the total size of the data uploaded may not exceed 40 MB.
UTF-8 filenames are supported, see examples.
You can also specify additional properties using form field:
- metadata could be passed usingmetadataform field. Metadata will
be set to newly created annotation object.
metadata
- values could be passed usingvaluesform field. It may
be used to initialize datapoint values by setting the value ofrir_field_namesin the schema.
values
rir_field_names
For exampleupload:organization_unitfield may be referenced in a schema like this:{
     "category": "datapoint",
     "id": "organization_unit",
     "label": "Org unit",
     "type": "string",
     "rir_field_names": ["upload:organization_unit"]
     ...
   }
upload:organization_unit

```
{
     "category": "datapoint",
     "id": "organization_unit",
     "label": "Org unit",
     "type": "string",
     "rir_field_names": ["upload:organization_unit"]
     ...
   }
```

Upload endpoint also supportsbasic authenticationto enable easy integration
with third-party systems.

#### Response

Status:201
201
Response contains a list of annotations and documents created. Top-level keysannotationanddocumentare obsolete and should be ignored.
annotation
document
Example upload response

```
{
  "results": [
    {
      "annotation": "https://.rossum.app/api/v1/annotations/315509",
      "document": "https://.rossum.app/api/v1/documents/315609"
    },
    {
      "annotation": "https://.rossum.app/api/v1/annotations/315510",
      "document": "https://.rossum.app/api/v1/documents/315610"
    }
  ],
  "annotation": "https://.rossum.app/api/v1/annotations/315509",
  "document": "https://.rossum.app/api/v1/documents/315609"
}
```


### Export annotations

Download CSV file with selected columns from annotations315777and315778.
315777
315778

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=csv&columns=meta_file_name,document_id,date_issue,sender_name,amount_total&id=315777,315778'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=csv&columns=meta_file_name,document_id,date_issue,sender_name,amount_total&id=315777,315778'

```
meta_file_name,Invoice number,Invoice Date,Sender Name,Total amount
template_invoice.pdf,12345,2017-06-01,"Peter, Paul and Merry",900.00
quora.pdf,2183760194,2018-08-06,"Quora, Inc",500.00
```

meta_file_name,Invoice number,Invoice Date,Sender Name,Total amount
template_invoice.pdf,12345,2017-06-01,"Peter, Paul and Merry",900.00
quora.pdf,2183760194,2018-08-06,"Quora, Inc",500.00
Download CSV file with prepend_columns and append_columns from annotations315777and315778.
315777
315778

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=csv&prepend_columns=meta_file_name&append_columns=meta_url&id=315777,315778'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=csv&prepend_columns=meta_file_name&append_columns=meta_url&id=315777,315778'

```
meta_file_name,Invoice number,Invoice Date,Sender Name,Total amount,meta_url
template_invoice.pdf,12345,2017-06-01,"Peter, Paul and Merry",900.00,https://<example>.rossum.app/api/v1/annotations/315777
quora.pdf,2183760194,2018-08-06,"Quora, Inc",500.00,https://<example>.rossum.app/api/v1/annotations/315778
```

meta_file_name,Invoice number,Invoice Date,Sender Name,Total amount,meta_url
template_invoice.pdf,12345,2017-06-01,"Peter, Paul and Merry",900.00,https://<example>.rossum.app/api/v1/annotations/315777
quora.pdf,2183760194,2018-08-06,"Quora, Inc",500.00,https://<example>.rossum.app/api/v1/annotations/315778
Download CSV file for a specific page when downloading large amounts of data.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=csv&status=exported&page=1&page_size=1000'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=csv&status=exported&page=1&page_size=1000'
Download XML file with all exported annotations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=xml&status=exported'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=xml&status=exported'

```
<?xml version="1.0" encoding="utf-8"?><export><results><annotationurl="https://<example>.rossum.app/api/v1/annotations/315777"><status>exported</status><arrived_at>2019-10-13T21:33:01.509886Z</arrived_at><exported_at>2019-10-13T12:00:01.000133Z</exported_at><documenturl="https://<example>.rossum.app/api/v1/documents/315877"><file_name>template_invoice.pdf</file_name><file>https://<example>.rossum.app/api/v1/documents/315877/content</file></document><modifier/><schemaurl="https://<example>.rossum.app/api/v1/schemas/31336"/><metadata/><content><sectionschema_id="invoice_details_section"><datapointschema_id="document_id"type="string"rir_confidence="0.99">12345</datapoint>...</section></content></annotation></results><pagination><next/><previous/><total>1</total><total_pages>1</total_pages></pagination></export>
```

<?xml version="1.0" encoding="utf-8"?><export><results><annotationurl="https://<example>.rossum.app/api/v1/annotations/315777"><status>exported</status><arrived_at>2019-10-13T21:33:01.509886Z</arrived_at><exported_at>2019-10-13T12:00:01.000133Z</exported_at><documenturl="https://<example>.rossum.app/api/v1/documents/315877"><file_name>template_invoice.pdf</file_name><file>https://<example>.rossum.app/api/v1/documents/315877/content</file></document><modifier/><schemaurl="https://<example>.rossum.app/api/v1/schemas/31336"/><metadata/><content><sectionschema_id="invoice_details_section"><datapointschema_id="document_id"type="string"rir_confidence="0.99">12345</datapoint>...</section></content></annotation></results><pagination><next/><previous/><total>1</total><total_pages>1</total_pages></pagination></export>
Download JSON file with all exported annotations that were imported on October 13th 2019.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=json&status=exported&arrived_at_after=2019-10-13&arrived_at_before=2019-10-14'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=json&status=exported&arrived_at_after=2019-10-13&arrived_at_before=2019-10-14'

```
{"pagination":{"total":5,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/annotations/315777","status":"exported","arrived_at":"2019-10-13T21:33:01.509886Z","exported_at":"2019-10-14T12:00:01.000133Z","document":{"url":"https://<example>.rossum.app/api/v1/documents/315877","file_name":"template_invoice.pdf","file":"https://<example>.rossum.app/api/v1/documents/315877/content"},"modifier":null,"schema":{"url":"https://<example>.rossum.app/api/v1/schemas/31336"},"metadata":{},"content":[{"category":"section","schema_id":"invoice_details_section","children":[{"category":"datapoint","schema_id":"document_id","value":"12345","type":"string","rir_confidence":0.99},...]}]}]}
```

{"pagination":{"total":5,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/annotations/315777","status":"exported","arrived_at":"2019-10-13T21:33:01.509886Z","exported_at":"2019-10-14T12:00:01.000133Z","document":{"url":"https://<example>.rossum.app/api/v1/documents/315877","file_name":"template_invoice.pdf","file":"https://<example>.rossum.app/api/v1/documents/315877/content"},"modifier":null,"schema":{"url":"https://<example>.rossum.app/api/v1/schemas/31336"},"metadata":{},"content":[{"category":"section","schema_id":"invoice_details_section","children":[{"category":"datapoint","schema_id":"document_id","value":"12345","type":"string","rir_confidence":0.99},...]}]}]}
Download and set the status of annotations toexporting.
exporting

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?to_status=exporting&status=confirmed'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?to_status=exporting&status=confirmed'

```
{"pagination":{"total":5,"total_pages":1,"next":null,"previous":null},"results":[{"status":"exporting",...}]}
```

{"pagination":{"total":5,"total_pages":1,"next":null,"previous":null},"results":[{"status":"exporting",...}]}
GET /v1/queues/{id}/exportorPOST /v1/queues/{id}/export
GET /v1/queues/{id}/export
POST /v1/queues/{id}/export
confirmed
queue.use_confirmed_state = true
to_status
exporting
exported
Export annotations from the queue in XML, CSV or JSON format.
Output format is negotiated by Accept header orformatparameter. Supported formats are:csv,xml,xlsxandjson.
format
csv
xml
xlsx
json

#### Filters

Filters may be specified to limit annotations to be exported, all filters applicable to theannotation listare supported.
Multiple filter attributes are combined with AND, which results in more specific response.
The most common filters are eitherlist of idsor specifying atime period:
AttributeDescriptionidId of annotation to be exported, multiple ids may be separated by a comma.statusAnnotationstatusmodifierUser idarrived_at_beforeISO 8601 timestamp (e.g.arrived_at_before=2019-11-15)arrived_at_afterISO 8601 timestamp (e.g.arrived_at_after=2019-11-14)exported_at_beforeISO 8601 timestamp (e.g.exported_at_before=2019-11-14 22:00:00)exported_at_afterISO 8601 timestamp (e.g.exported_at_after=2019-11-14 12:00:00)export_failed_at_beforeISO 8601 timestamp (e.g.export_failed_at_before=2019-11-14 22:00:00)export_failed_at_afterISO 8601 timestamp (e.g.export_failed_at_after=2019-11-14 12:00:00)page_sizeNumber of the documents to be exported. To be used together withpageattribute. Seepagination.pageNumber of a page to be exported when using pagination. Useful for exports of large amounts of data. To be used together with thepage_sizeattribute.to_statusstatusof annotations under export is switched to definedto_statusstate (useful whenqueue.use_confirmed_state = true). This parameter is only valid with POST method,statuscan be changed only toexporting(export will be initiated asynchronously and status will be moved toexportedautomatically after successful export) orexported(export will be initiated sychronously). Annotations with current statusexportedorexportingare left untouched.
arrived_at_before=2019-11-15
arrived_at_after=2019-11-14
exported_at_before=2019-11-14 22:00:00
exported_at_after=2019-11-14 12:00:00
export_failed_at_before=2019-11-14 22:00:00
export_failed_at_after=2019-11-14 12:00:00
page
page_size
status
to_status
queue.use_confirmed_state = true
status
exporting
exported
exported
exported
exporting
search

#### Response

Status:200
200
Returnspaginatedresponse that contains annotation data in one of the following format.
Columns included in CSV output are defined bycolumns,prepend_columnsandappend_columnsURL parameters.prepend_columnsparameter defines columns at the beginning of the row whileappend_columnsat the end. All stated parameters
are specified by datapoint schema ids and meta-columns. Default is to export
all fields defined in a schema.
columns
prepend_columns
append_columns
prepend_columns
append_columns
Supported meta-columns are:meta_arrived_at,meta_file,meta_file_name,meta_status,meta_url,meta_automated,meta_modified_at,meta_assigned_at.
meta_arrived_at
meta_file
meta_file_name
meta_status
meta_url
meta_automated
meta_modified_at
meta_assigned_at
CSV format can be fine-tuned by following query parameters:
- delimiter- one-character string used to separate fields. It defaults to ','.
delimiter
- quote_char- one-character string used to quote fields containing special characters, such as the delimiter or quotechar, or which contain new-line characters. It defaults to '"'.
quote_char
- quoting- controls when quotes should be generated by the writer and recognised by the reader. It can take on any of thequote_minimal,quote_none,quote_all,quote_non_numeric. Ifquote_noneis specified,escape_charis mandatory.
quoting
quote_minimal
quote_none
quote_all
quote_non_numeric
quote_none
escape_char
- escape_char- one-character string used by the writer to escape the delimiter.
escape_char
XLSX export behaves exactly same as CSV export, including URL parameters.
The only difference is output format.
XML format is described by XML Schema Definitionqueues_export.xsd.
JSON format uses format similar to the XML format above.

### Get suggested email recipients

Get315777,78590annotations and7524email_hooks suggested email recipients
315777
78590
7524

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/315777", https://<example>.rossum.app/api/v1/annotations/78590], "email_threads": ["https://<example>.rossum.app/api/v1/email_threads/7524"]}'\'https://<example>.rossum.app/api/v1/queues/246/suggested_recipients'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/315777", https://<example>.rossum.app/api/v1/annotations/78590], "email_threads": ["https://<example>.rossum.app/api/v1/email_threads/7524"]}'\'https://<example>.rossum.app/api/v1/queues/246/suggested_recipients'

```
{"results":[{"source":"email_header","email":"don.joe@corp.us","name":"Don Joe"},...]}
```

{"results":[{"source":"email_header","email":"don.joe@corp.us","name":"Don Joe"},...]}
POST /v1/queues/{id}/suggested_recipients
POST /v1/queues/{id}/suggested_recipients
Retrieves suggested email recipients depending on Queuessuggested recipients settings.
AttributeTypeDescriptionannotationslistList ofannotationurlsemail_threadslistList ofemail threadurls

#### Response

Status:200
200
Returns a list ofsource objects.

#### Suggested recipients source object

ParameterDescriptionsourceSpecifies where the email is found, seepossible sourcesemailEmail address of the suggested recipientnameName of the suggested recipient. Either a value from an email header or a value from parsing the email address

### List all queues

List all queues in workspace7540ordered byname
7540
name

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues?workspace=7540&ordering=name'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues?workspace=7540&ordering=name'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":8199,"name":"Receipts","url":"https://<example>.rossum.app/api/v1/queues/8199","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540",...},{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540",...}]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":8199,"name":"Receipts","url":"https://<example>.rossum.app/api/v1/queues/8199","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540",...},{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540",...}]}
GET /v1/queues
GET /v1/queues
Retrieve all queue objects.
Supported ordering:id,name,workspace,connector,webhooks,schema,inbox,locale
id
name
workspace
connector
webhooks
schema
inbox
locale

#### Filters

AttributeDescriptionidId of a queuenameName of a queueworkspaceId of a workspaceinboxId of an inboxconnectorId of a connectorwebhooksIds of hookshooksIds of hookslocaleQueue object localededicated_engineId of a dedicated enginegeneric_engineId of a generic enginedeletingBool filter - queue is being deleted (delete_afteris set)
delete_after

#### Response

Status:200
200
Returnspaginatedresponse with a list ofqueueobjects.

### Create new queue

Create new queue in workspace7540namedTest Queue
7540

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Queue", "workspace": "https://<example>.rossum.app/api/v1/workspaces/7540", "schema": "https://<example>.rossum.app/api/v1/schemas/31336", "generic_engine": "https://<example>.rossum.app/api/v1/generic_engines/9876"}'\'https://<example>.rossum.app/api/v1/queues'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Queue", "workspace": "https://<example>.rossum.app/api/v1/workspaces/7540", "schema": "https://<example>.rossum.app/api/v1/schemas/31336", "generic_engine": "https://<example>.rossum.app/api/v1/generic_engines/9876"}'\'https://<example>.rossum.app/api/v1/queues'

```
{"id":8236,"name":"Test Queue","url":"https://<example>.rossum.app/api/v1/queues/8236","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876",...}
```

{"id":8236,"name":"Test Queue","url":"https://<example>.rossum.app/api/v1/queues/8236","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876",...}
POST /v1/queues
POST /v1/queues
Create a newqueueobject.

#### Response

Status:201
201
Returns createdqueueobject.

#### Create queue from template organization

Create new queue object from template organization, see available templates inorganization.
Create new queue object from template organization

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test queue", "template_name": "EU Demo Template", "workspace": "https://<example>.rossum.app/api/v1/workspaces/489", "include_documents": false}'\'https://<example>.rossum.app/api/v1/queues/from_template'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test queue", "template_name": "EU Demo Template", "workspace": "https://<example>.rossum.app/api/v1/workspaces/489", "include_documents": false}'\'https://<example>.rossum.app/api/v1/queues/from_template'

```
{"id":8236,"name":"Test Queue","url":"https://<example>.rossum.app/api/v1/queues/8236",...}
```

{"id":8236,"name":"Test Queue","url":"https://<example>.rossum.app/api/v1/queues/8236",...}
POST /v1/queues/from_template
POST /v1/queues/from_template
Create a new queue object.
AttributeDescriptionnameName of a queuetemplate_nameTemplate to use for new queueworkspaceId of a workspaceinclude_documentsWhether to copy documents from the template queue

#### Response

Status:201
201
Returns createdqueueobject.

### Retrieve a queue

Get queue object8198
8198

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8198'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8198'

```
{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876",...}
```

{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876",...}
GET /v1/queues/{id}
GET /v1/queues/{id}
Get a queue object.

#### Response

Status:200
200
Returnsqueueobject.

### Update a queue

Update queue object8236
8236

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "My Queue", "workspace": "https://<example>.rossum.app/api/v1/workspaces/7540", "schema": "https://<example>.rossum.app/api/v1/schemas/31336", "generic_engine": "https://<example>.rossum.app/api/v1/generic_engines/9876"}'\'https://<example>.rossum.app/api/v1/queues/8236'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "My Queue", "workspace": "https://<example>.rossum.app/api/v1/workspaces/7540", "schema": "https://<example>.rossum.app/api/v1/schemas/31336", "generic_engine": "https://<example>.rossum.app/api/v1/generic_engines/9876"}'\'https://<example>.rossum.app/api/v1/queues/8236'

```
{"id":8236,"name":"My Queue","url":"https://<example>.rossum.app/api/v1/queues/8236","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876",...}
```

{"id":8236,"name":"My Queue","url":"https://<example>.rossum.app/api/v1/queues/8236","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876",...}
PUT /v1/queues/{id}
PUT /v1/queues/{id}
Update queue object.

#### Response

Status:200
200
Returns updatedqueueobject.

### Update part of a queue

Update name of queue object8236
8236

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "New Queue"}'\'https://<example>.rossum.app/api/v1/queues/8236'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "New Queue"}'\'https://<example>.rossum.app/api/v1/queues/8236'

```
{"id":8236,"name":"New Queue","url":"https://<example>.rossum.app/api/v1/queues/8236","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540",...}
```

{"id":8236,"name":"New Queue","url":"https://<example>.rossum.app/api/v1/queues/8236","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540",...}
PATCH /v1/queues/{id}
PATCH /v1/queues/{id}
Update part of queue object.

#### Response

Status:200
200
Returns updatedqueueobject.

### Duplicate a queue

Duplicate existing queue object8236
8236

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Duplicate Queue", "copy_extensions_settings": true, "copy_email_settings": true, "copy_automation_setting": true, "copy_permissions": true, "copy_rules_and_actions": true}'\'https://<example>.rossum.app/api/v1/queues/8236/duplicate'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Duplicate Queue", "copy_extensions_settings": true, "copy_email_settings": true, "copy_automation_setting": true, "copy_permissions": true, "copy_rules_and_actions": true}'\'https://<example>.rossum.app/api/v1/queues/8236/duplicate'

```
{"id":8237,"name":"Duplicate Queue","url":"https://<example>.rossum.app/api/v1/queues/8237",...}
```

{"id":8237,"name":"Duplicate Queue","url":"https://<example>.rossum.app/api/v1/queues/8237",...}
POST /v1/queues/{id}/duplicate
POST /v1/queues/{id}/duplicate
Duplicate a queue object.
AttributeTypeDefaultDescriptionnamestringName of the duplicated queue.copy_extensions_settingsbooltrueWhether to copyhooks.copy_email_settingsbooltrueWhether to copyemail notifications settings.copy_delete_recommendationsbooltrueWhether to copydelete recommendations.copy_automation_settingsbooltrueWhether to copyautomation level,automation settingsandautomation_enabledqueue settingssettings.copy_permissionsbooltrueWhether to copyusersandmemberships.copy_rules_and_actionsbooltrueWhether to copyrules.
automation_enabled

#### Response

Status:201
201
Returns duplicate ofqueueobject.

### Delete a queue

Delete queue8236
8236

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236'
DELETE /v1/queues/{id}
DELETE /v1/queues/{id}
Delete queue object.
Calling this endpoint will schedule the queue to be asynchronously deleted. The only synchronous operations are
- setdelete_after
delete_after
- changestatustodeletion_requested(seequeue status)
status
deletion_requested
- unlink workspace
- the above will result in queue not being visible in the Rossum UI
- importing docs to the queue is disabled (viauploadas well asemail import)
By default, the deletion will start after 24 hours. You can change this behaviour by specifyingdelete_afterquery parameter.
delete_after

#### Query parameters

KeyTypeDefault valueDescriptiondelete_aftertimedelta24:00:00The queue deletion will be postponed by the given time delta.
24:00:00

#### Response

Status:202
202

### Start annotation

POST /v1/queues/{id}/next
POST /v1/queues/{id}/next
Start reviewing the next available annotation from the queue by the calling user.
This endpoint isINTERNALand may change in the future.
Request body:
AttributeTypeDescriptionannotation_idslist[integer]List of annotation ids to select from (optional).statuseslist[string]List of allowed statuses (optional).

#### Response

Status:200
200
Result object:
AttributeTypeDescriptionannotationURLURL of started annotation.session_timeoutstringSession timeout in format HH:MM:SS.
If there is no annotation to start status200is returned with body:{"annotation": null}
200
{"annotation": null}

### Get counts of related objects

Get counts of related objects for queue8236
8236

```
curl-XGET-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/related_objects_counts'
```

curl-XGET-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/related_objects_counts'

```
{"annotations":123,"emails":456,"trained_dedicated_engines":2}
```

{"annotations":123,"emails":456,"trained_dedicated_engines":2}
GET /v1/queues/{id}/related_objects_counts
GET /v1/queues/{id}/related_objects_counts
Get counts of selected related objects for a queue.
AttributeTypeDescriptionemailsintegerNumber of email objects related to the queueannotationsintegerNumber of annotation objects related to the queue (purged annotations are excluded from this count)trained_dedicated_enginesintegerNumber of dedicated engines using the queue for training

#### Response

Status:200
200


## Relation

Example relation object

```
{"id":1,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/1"}
```

{"id":1,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/1"}
A relation object introduce common relations between annotations. An annotation could be related to one or more other annotations and
it may belong to several relations at the same time.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the relationtruetypestringeditType of relationship. Possible values areedit,attachmentorduplicate. SeebelowkeystringKey used to distinguish several instances of the same typeparentURLURL of the parent annotation in case of 1-M relationshipannotationslist[URL]List of related annotationsurlURLURL of the relationtrue
edit
edit
attachment
duplicate

#### Relation types:

- editrelation is created after editing annotation in user interface (rotation or split of the document). The original annotation is set toparentattribute and newly created
annotations are set toannotationsattribute. To find all siblings of edited annotation seefilters on annotation
edit
parent
annotations
- attachmentis a relationship representing the state that one or more documents are attachments to another document.keyis null in this case. Feature must be enabled.
attachment
key
- duplicaterelation is created after importing the same document that already exists in Rossum for current organization.
Ifduplicaterelation already exists then corresponding annotation is added to existing relation.keyofduplicaterelation is set to MD5 hash of document content.
To find all duplicates of the annotation filter annotations with appropriate MD5 hash in relationkey. Seefilters on annotation
duplicate
duplicate
key
duplicate
key

### List all relations

List all relations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/relations'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/relations'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/456","https://<example>.rossum.app/api/v1/annotations/457"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/456","https://<example>.rossum.app/api/v1/annotations/457"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}]}
GET /v1/relations
GET /v1/relations
Retrieve all relation objects (annotations from queues not withactivestatusare excluded).
active
Supported filters:
AttributeDescriptionidId of the relation. Multiple values may be separated using a comma.typeRelationtype. Multiple values may be separated using a comma.parentId of parent annotation. Multiple values may be separated using a comma.keyRelation keyannotationId of related annotation. Multiple values may be separated using a comma.
Supported ordering:type,parent,key
type
parent
key
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofrelationobjects.

### Create a new relation

Create a new relation of type edit

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "edit", "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124"]}'\'https://<example>.rossum.app/api/v1/relations'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "edit", "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124"]}'\'https://<example>.rossum.app/api/v1/relations'

```
{"id":789,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124"],"url":"https://<example>.rossum.app/api/v1/relations/789"}
```

{"id":789,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124"],"url":"https://<example>.rossum.app/api/v1/relations/789"}
Create a new attachment. Annotation 123 will have an attachment 124.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "attachment", "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124"]}'\'https://<example>.rossum.app/api/v1/relations'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "attachment", "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124"]}'\'https://<example>.rossum.app/api/v1/relations'

```
{"id":787,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124"],"url":"https://<example>.rossum.app/api/v1/relations/787"}
```

{"id":787,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124"],"url":"https://<example>.rossum.app/api/v1/relations/787"}
POST /v1/relations
POST /v1/relations
Create a new relation object.

#### Response

Status:201
201
Returns createdrelationobject.

### Retrieve a relation

Get relation object1500
1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/relations/1500'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/relations/1500'

```
{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}
```

{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}
GET /v1/relations/{id}
GET /v1/relations/{id}
Get an relation object.

#### Response

Status:200
200
Returnsrelationobject.

### Update a relation

Update the relation object1500
1500

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "edit", "key": None, "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124"} \
  'https://<example>.rossum.app/api/v1/relations/1500'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "edit", "key": None, "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124"} \
  'https://<example>.rossum.app/api/v1/relations/1500'

```
{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}
```

{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}
Attachment update. Annotation 123 will have two attachments: 124 and 125.

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "attachment", "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124", "https://<example>.rossum.app/api/v1/annotations/125"]}'\'https://<example>.rossum.app/api/v1/relations/787'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "attachment", "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124", "https://<example>.rossum.app/api/v1/annotations/125"]}'\'https://<example>.rossum.app/api/v1/relations/787'

```
{"id":787,"type":"attachment","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/787"}
```

{"id":787,"type":"attachment","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/787"}
PUT /v1/relations/{id}
PUT /v1/relations/{id}
Update relation object.

#### Response

Status:200
200
Returns updatedrelationobject.

### Update part of a relation

Update relation annotations on relation object1500
1500

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/124", "https://<example>.rossum.app/api/v1/annotations/125"]}'\'https://<example>.rossum.app/api/v1/relations/1500'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/124", "https://<example>.rossum.app/api/v1/annotations/125"]}'\'https://<example>.rossum.app/api/v1/relations/1500'

```
{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}
```

{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}
Attachment partial update. Annotation 123 will have just one attachment 125.

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/125"]}'\'https://<example>.rossum.app/api/v1/relations/787'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/125"]}'\'https://<example>.rossum.app/api/v1/relations/787'

```
{"id":787,"type":"attachment","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/787"}
```

{"id":787,"type":"attachment","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/787"}
PATCH /v1/relations/{id}
PATCH /v1/relations/{id}
Update part of relation object.

#### Response

Status:200
200
Returns updatedrelationobject.

### Delete a relation

Delete relation1500
1500

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/relations/1500'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/relations/1500'
DELETE /v1/relations/{id}
DELETE /v1/relations/{id}
Delete relation object.

#### Response

Status:204
204


## Rule

Example rule object

```
{"id":123,"url":"https://<example>.rossum.app/api/v1/rules/123","name":"rule","enabled":true,"organization":"https://<example>.rossum.app/api/v1/organizationss/1001","schema":"https://<example>.rossum.app/api/v1/schemas/1001","trigger_condition":"True","created_by":"https://<example>.rossum.app/api/v1/users/9524","created_at":"2022-01-01T15:02:25.653324Z","modified_by":"https://<example>.rossum.app/api/v1/users/2345","modified_at":"2020-01-01T10:08:03.856648Z","rule_template":null,"synchronized_from_template":false,"actions":[{"id":"f3c43f16-b5f1-4ac8-b789-17d4c26463d7","enabled":true,"type":"show_message","payload":{"type":"error","content":"Error message!","schema_id":"invoice_id"},"event":"validation"}]}
```

{"id":123,"url":"https://<example>.rossum.app/api/v1/rules/123","name":"rule","enabled":true,"organization":"https://<example>.rossum.app/api/v1/organizationss/1001","schema":"https://<example>.rossum.app/api/v1/schemas/1001","trigger_condition":"True","created_by":"https://<example>.rossum.app/api/v1/users/9524","created_at":"2022-01-01T15:02:25.653324Z","modified_by":"https://<example>.rossum.app/api/v1/users/2345","modified_at":"2020-01-01T10:08:03.856648Z","rule_template":null,"synchronized_from_template":false,"actions":[{"id":"f3c43f16-b5f1-4ac8-b789-17d4c26463d7","enabled":true,"type":"show_message","payload":{"type":"error","content":"Error message!","schema_id":"invoice_id"},"event":"validation"}]}
Rule object represents arbitrary business rules added toschemaobjects.
AttributeTypeRead-onlyDescriptionidintegeryesRule object ID.urlURLyesRule object URL.namestringnoName of the rule.trigger_conditionstringnoA condition for triggering the rule's actions. (default:"True"). This is a formula evaluated byRossum TxScript.organizationURLyesOrganization the rule belongs to.schemaURLnoSchema the rule belongs to.rule_templateURLno(optional) Rule template the rule was created from.synchronized_from_templateboolnoSignals whether the rule is automatically updated from the linked template. (default:false)created_byURLnoUser who created the rule.created_atdatetimenoTimestamp of the rule creation.modified_byURLnoUser who was the last to modify the rule.modified_atdatetimenoTimestamp of the latest modification.actionslist[object]noList of the rule action objects (Seerule actions.enabledboolnoIf false the rule is disabled (default:true)
"True"
false
true

### Trigger condition

Thetrigger_conditionis aTxScriptformula which controls the execution of the list of actions in a rule object.
trigger_condition
There are two possible evaluation modes for this condition:
- simple mode: when the condition does not reference any datapoint, or only reference header fields. Example:len(field.document_id) < 10.
len(field.document_id) < 10
- line-item mode: when the condition references a line item datapoint (a column of a multivalue table). Examplefield.item_amount > 100.0.
field.item_amount > 100.0
In line item mode, the condition is evaluatedonce for each row of the table, which means multiple actions can potentially be executed. In this case, a deduplication mechanism prevents the creation of duplicate messages (show_messageaction), duplicate blockers (add_automation_blockeraction), and identical emails from being sent (send_emailaction).
show_message
add_automation_blocker
send_email

### Rule actions

Object defines rule actions to be executed when trigger condition is met.
AttributeTypeRead-onlyDescriptionidstringnoRule action ID. Needs to be unique within the Rule'sactions.enabledboolnoIf false the action is disabled (default:true).typestringnoSee the following for the list of possible actions.payloadobjectnoSee the following for the payload structure for each action.eventobjectnoActions are configured to be executed on a specific event, seetrigger events.
actions
true
Note that just after document import, the initial validation is performed and rules are then executed: 
the trigger conditions are first evaluated on the latest anntoation content, and then actions registered onvalidationandannotation_importedevents are both executed.
validation
annotation_imported

#### Action Show message

Action:show_message
show_message
Event: can be triggered onvalidationevent only.
validation
Payload:
AttributeTypeDescriptiontypestringOne of:error,warning,info.contentstringMessage content to be displayed.schema_idOptional[string]Optional message target field (omit for document scope message).
error
warning
info

#### Action Add automation blocker

Action:add_automation_blocker
add_automation_blocker
Event: can be triggered onvalidationevent only.
validation
Payload:
AttributeTypeDescriptioncontentstringAutomation blocker content to be displayed.schema_idOptional[string]Optional automation blocker target field id (omit for document scope automation blocker).
Note: at most one action of typeadd_automation_blockercan be set up for oneruleobject.
add_automation_blocker

#### Action change status

Action:change_status
change_status
Event: can be triggered onannotation_importedevent only.
annotation_imported
Payload:
AttributeTypeDescriptionmethodstringPossible options:postpone,export,delete,confirm,reject.
postpone
export
delete
confirm
reject
Note: at most one action of typechange_statuscan be set up for oneruleobject.
change_status

#### Action Change queue

This action moves the annotation to another queue with or without re-extraction of the data (see thereimportflag).
reimport
Action:change_queue
change_queue
Event: Can be configured to trigger onannotation_imported,annotation_confirmedorannotation_exported.
annotation_imported
annotation_confirmed
annotation_exported
Payload:
AttributeTypeDescriptionreimportOptional[bool]Flag that controls whether the annotation will be reimported during the action execution.queue_idintegerID of the target queue.
Note: at most one action of typechange_queuecan be set up for oneruleobject.
change_queue

#### Action Add label

Action:add_label
add_label
Event: can be triggered onvalidationevent only.
validation
Payload:
AttributeTypeDescriptionlabelslist[url]URLs oflabelobject to be linked to the processedannotation.
Note: at most one action of typeadd_labelcan be set up for oneruleobject.
add_label

#### Action Remove label

Action:remove_label
remove_label
Event: can be triggered onvalidationevent only.
validation
Payload:
AttributeTypeDescriptionlabelslist[url]URLs oflabelobject to be unlinked from the processedannotation.
Note: at most one action of typeremove_labelcan be set up for oneruleobject.
remove_label

#### Action Add / Remove label

Action:add_remove_label
add_remove_label
Event: can be triggered onvalidationevent only.
validation
Payload:
AttributeTypeDescriptionlabelslist[url]URLs oflabelobject to be linked to the processedannotation.
The affected labels are added to the annotation when the condition is satisfied, and removed otherwise.
Note: at most one action of typeadd_remove_labelcan be set up for oneruleobject.
add_remove_label

#### Action Show / hide field

Action:show_hide_field
show_hide_field
Event: can be triggered onvalidationevent only.
validation
Payload:
AttributeTypeDescriptionschema_idsList[string]Sethiddenattribute of schema fields according to condition. (Please seeschema content).
hidden
The affected schema field is visible when the condition is satisfied, and is hidden otherwise.

#### Action Show field

Action:show_field
show_field
Event: can be triggered onvalidationevent only.
validation
Payload:
AttributeTypeDescriptionschema_idsList[string]Sethiddenattribute of schema fields toFalse. (Please seeschema content).
hidden
False
Note: at most one action of typeshow_fieldcan be set up for oneruleobject.
show_field

#### Action Hide field

Action:hide_field
hide_field
Event: can be triggered onvalidationevent only.
validation
Payload:
AttributeTypeDescriptionschema_idsList[string]Sethiddenattribute of schema fields toTrue. (Please seeschema content).
hidden
True
Note: at most one action of typehide_fieldcan be set up for oneruleobject.
hide_field

#### Action Add validation source

Addsrulesvalidation source to a datapoint.
rules
Action:add_validation_source
add_validation_source
Event: can be triggered onvalidationevent only.
validation
Payload:
AttributeTypeDescriptionschema_idstringSchema ID of the datapoint to add the validation source to (Please seeschema content).
Note: at most one action of typeadd_validation_sourcecan be set up for oneruleobject.
add_validation_source

#### Action send email

In line item mode of execution, deduplication mechanism will prevent multiple identical emails from being sent, and at mostfiveemails can be sent by a single action.
Action:send_email
send_email
Event: Can be configured to trigger onannotation_imported,annotation_confirmedorannotation_exported.
annotation_imported
annotation_confirmed
annotation_exported
Payload:
Ifemail_templateis defined, the rest of the attributes are ignored.
email_template
AttributeTypeDescriptionRequiredemail_templatestringEmail template URL.Yesattach_documentbooleanWhen true document linked to the annotation will be sent together with the email as an attachment (defaultFalse).No
False
Ifemail_templateis not defined, then the payload can contain the following attributes:
email_template
AttributeTypeDescriptionRequiredtoList[string]List of recipients.YessubjectstringSubject of the email.YesbodystringBody of the email.YesccList[string]List of cc.NobccList[string]List of bcc.No

### List all rules

List all rules

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/rules'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/rules'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/rules/1",...}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/rules/1",...}]}
GET /v1/rules
GET /v1/rules
List all rules objects.
Supported filters:id,queue,enabled,linked,actions,schema,rule_template,name,organization
id
queue
enabled
linked
actions
schema
rule_template
name
organization
Supported ordering:id,name,organization
id
name
organization
FilterTypeDescriptionactionslist[str]Comma separated list of action types (e.g.show_message,change_queue)linkedbooleanList onlylinked/unlinkedrules (linked rules have more than one queue connected)enabledbooleanList onlyenabled/disabledrulesqueuelist[int]List rules by queue idsidlist[int]List rules by rule ids
show_message,change_queue
linked
unlinked
enabled
disabled
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofruleobjects.

### Retrieve rule

Get rule object123
123

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/rules/123'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/rules/123'

```
{"id":123,"url":"https://<example>.rossum.app/api/v1/rules/123",...}
```

{"id":123,"url":"https://<example>.rossum.app/api/v1/rules/123",...}
GET /v1/rules/{id}
GET /v1/rules/{id}
Retrieve a rule object.

#### Response

Status:200
200
Returnsruleobject.

### Create a new rule

Create new rule

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "rule", "organization": "https://<example>.rossum.app/api/v1/organization/1", "schema": "https://<example>.rossum.app/api/v1/schemas/442"}'\'https://<example>.rossum.app/api/v1/rules'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "rule", "organization": "https://<example>.rossum.app/api/v1/organization/1", "schema": "https://<example>.rossum.app/api/v1/schemas/442"}'\'https://<example>.rossum.app/api/v1/rules'

```
{"id":42,"url":"https://<example>.rossum.app/api/v1/rules/42",...}
```

{"id":42,"url":"https://<example>.rossum.app/api/v1/rules/42",...}
POST /v1/rules
POST /v1/rules
Create a new rule object.

#### Response

Status:201
201
Returns createdruleobject.

### Update part of a rule

Update content of rule object42
42

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Block automation when invoice is missing"}'\'https://<example>.rossum.app/api/v1/rules/42'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Block automation when invoice is missing"}'\'https://<example>.rossum.app/api/v1/rules/42'

```
{"id":42,"url":"https://<example>.rossum.app/api/v1/rules/42",...}
```

{"id":42,"url":"https://<example>.rossum.app/api/v1/rules/42",...}
PATCH /v1/rules/{id}
PATCH /v1/rules/{id}
Update part of rule object.

#### Response

Status:200
200
Returns updatedruleobject.

### Update a rule

Update rule object42
42

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "rule", "organization": "https://<example>.rossum.app/api/v1/organization/1", "schema": "https://<example>.rossum.app/api/v1/schemas/442"}'\'https://<example>.rossum.app/api/v1/rules/42'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "rule", "organization": "https://<example>.rossum.app/api/v1/organization/1", "schema": "https://<example>.rossum.app/api/v1/schemas/442"}'\'https://<example>.rossum.app/api/v1/rules/42'

```
{"id":42,"url":"https://<example>.rossum.app/api/v1/rules/42",...}
```

{"id":42,"url":"https://<example>.rossum.app/api/v1/rules/42",...}
PUT /v1/rules/{id}
PUT /v1/rules/{id}
Update rule object.

#### Response

Status:200
200
Returns updatedruleobject.

### Delete a rule

Delete rule42
42

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/rules/42'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/rules/42'
DELETE /v1/rules/{id}
DELETE /v1/rules/{id}
Delete rule object.

#### Response

Status:204
204


## Schema

Example schema object

```
{"id":31336,"name":"Basic Schema","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"url":"https://<example>.rossum.app/api/v1/schemas/31336","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","description":"section description","children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"],"constraints":{"required":false},"default_value":null},...]},...],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":31336,"name":"Basic Schema","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"url":"https://<example>.rossum.app/api/v1/schemas/31336","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","description":"section description","children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"],"constraints":{"required":false},"default_value":null},...]},...],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
A schema object specifies the set of datapoints that are extracted from the
document. For more information seeDocument Schema.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the schematruenamestringName of the schema (not visible in UI)urlURLURL of the schematruequeueslist[URL]List of queues that use schema object.truecontentlist[object]List of sections (top-level schema objects, seeDocument Schemafor description of schema)metadataobject{}Client data.modified_byURLnullLast modifier.truemodified_atdatetimenullDate of last modification.true
{}

### Validate a schema

Validate content of schema object

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","icon": null,"children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"]}]}]}'\'https://<example>.rossum.app/api/v1/schemas/validate'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","icon": null,"children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"]}]}]}'\'https://<example>.rossum.app/api/v1/schemas/validate'
POST /v1/schemas/validate
POST /v1/schemas/validate
Validate schema object, check for errors.

#### Response

Status:200
200
Returns 200 and error description in case of validation failure.

### List all schemas

List all schemas

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/schemas'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/schemas'

```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":31336,"url":"https://<example>.rossum.app/api/v1/schemas/31336"},{"id":33725,"url":"https://<example>.rossum.app/api/v1/schemas/33725"}]}
```

{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":31336,"url":"https://<example>.rossum.app/api/v1/schemas/31336"},{"id":33725,"url":"https://<example>.rossum.app/api/v1/schemas/33725"}]}
GET /v1/schemas
GET /v1/schemas
Retrieve all schema objects.
Supported filters:id,name,queue
id
name
queue
Supported ordering:id
id
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofschemaobjects.

### Create a new schema

Create new empty schema

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Schema", "content": []}'\'https://<example>.rossum.app/api/v1/schemas'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Schema", "content": []}'\'https://<example>.rossum.app/api/v1/schemas'

```
{"id":33725,"name":"Test Schema","queues":[],"url":"https://<example>.rossum.app/api/v1/schemas/33725","content":[],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":33725,"name":"Test Schema","queues":[],"url":"https://<example>.rossum.app/api/v1/schemas/33725","content":[],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
POST /v1/schemas
POST /v1/schemas
Create a new schema object.

#### Response

Status:201
201
Returns createdschemaobject.

#### Create schema from template organization

Create new schema object from template organization, see available templates inorganization.
Create new schema object from template organization

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Schema", "template_name": "EU Demo Template"}'\'https://<example>.rossum.app/api/v1/schemas/from_template'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Schema", "template_name": "EU Demo Template"}'\'https://<example>.rossum.app/api/v1/schemas/from_template'

```
{"name":"Test Schema","id":33726,"queues":[],"url":"https://<example>.rossum.app/api/v1/schemas/33726","content":[{"id":"invoice_info_section","icon":null,"label":"Basic information","category":"section","children":[...]}],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"name":"Test Schema","id":33726,"queues":[],"url":"https://<example>.rossum.app/api/v1/schemas/33726","content":[{"id":"invoice_info_section","icon":null,"label":"Basic information","category":"section","children":[...]}],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
POST /v1/schemas/from_template
POST /v1/schemas/from_template
Create a new schema object.

#### Response

Status:201
201
Returns createdschemaobject.

### Retrieve a schema

Get schema object31336
31336

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/schemas/31336'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/schemas/31336'

```
{"id":31336,"name":"Basic schema","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"url":"https://<example>.rossum.app/api/v1/schemas/31336","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","description":"section description","children":[{"category":"datapoint","id":"document_id","label":"Invoice number","description":"datapoint description","type":"string","rir_field_names":["document_id"],"constraints":{"required":false},"default_value":null},...]},...]}
```

{"id":31336,"name":"Basic schema","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"url":"https://<example>.rossum.app/api/v1/schemas/31336","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","description":"section description","children":[{"category":"datapoint","id":"document_id","label":"Invoice number","description":"datapoint description","type":"string","rir_field_names":["document_id"],"constraints":{"required":false},"default_value":null},...]},...]}
GET /v1/schemas/{id}
GET /v1/schemas/{id}
Get a schema object.

#### Response

Status:200
200
Returnsschemaobject.

### Update a schema

Update content of schema object33725
33725

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name":"Test Schema","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","icon": null,"children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"]}]}]}'\'https://<example>.rossum.app/api/v1/schemas/33725'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name":"Test Schema","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","icon": null,"children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"]}]}]}'\'https://<example>.rossum.app/api/v1/schemas/33725'

```
{"id":33725,"name":"Test Schema","queues":[],"url":"https://<example>.rossum.app/api/v1/schemas/33725","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"],"default_value":null}],"icon":null}],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":33725,"name":"Test Schema","queues":[],"url":"https://<example>.rossum.app/api/v1/schemas/33725","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"],"default_value":null}],"icon":null}],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
PUT /v1/schemas/{id}
PUT /v1/schemas/{id}
Update schema object. SeeUpdating schemafor more details about consequences of schema update.

#### Response

Status:200
200
Returns updatedschemaobject.

### Update part of a schema

Update  schema object31336
31336

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","icon": null,"children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"]}]}]}'\'https://<example>.rossum.app/api/v1/schemas/31336'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","icon": null,"children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"]}]}]}'\'https://<example>.rossum.app/api/v1/schemas/31336'

```
{"id":31336,"name":"New Schema","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"url":"https://<example>.rossum.app/api/v1/schemas/31336","content":[],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

{"id":31336,"name":"New Schema","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"url":"https://<example>.rossum.app/api/v1/schemas/31336","content":[],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
PATCH /v1/schemas/{id}
PATCH /v1/schemas/{id}
Update part of schema object. SeeUpdating schemafor more details about consequences of schema update.

#### Response

Status:200
200
Returns updatedschemaobject.

### Delete a schema

Delete schema31336
31336

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/schemas/31336'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/schemas/31336'
DELETE /v1/schemas/{id}
DELETE /v1/schemas/{id}
Delete schema object.

#### Response

Status:204
204


## Suggested edit

Example suggested edit object

```
{"id":314528,"url":"https://<example>.rossum.app/api/v1/suggested_edits/314528","annotation":"https://<example>.rossum.app/api/v1/annotations/314528","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314554","rotation":0},{"page":"https://<example>.rossum.app/api/v1/pages/314593","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}},{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314556","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}}]}
```

{"id":314528,"url":"https://<example>.rossum.app/api/v1/suggested_edits/314528","annotation":"https://<example>.rossum.app/api/v1/annotations/314528","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314554","rotation":0},{"page":"https://<example>.rossum.app/api/v1/pages/314593","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}},{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314556","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}}]}
A suggested edit object contains splittings of incomming document suggested by the AI engine.
Suggested edit objects are created automatically during document import.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the suggested edit.TrueurlURLURL of the suggested edit.TrueannotationURLAnnotation that suggested edit is related to.documentslist[Document split descriptor]List of document split descriptors.

### Document split descriptor

AttributeTypeDefaultDescriptionpageslist[Page descriptor]List of pages that should be split.target_queueURLTarget queue for the suggested split.valuesobject{}Edit valuesto be propagated to newly created annotations. Keys must be prefixed with "edit:", e.g. "edit:document_type".Schema Datapoint descriptiondescribes how it is used to initialize datapoint value.

### Page descriptor

AttributeTypeDefaultDescriptionpageURLPage to split.rotationinteger0Rotation of the page.deletedbooleanfalseIndicates whether the page is marked as deleted.

### List all suggested_edit objects

List all suggested_edit objects

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/suggested_edits'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/suggested_edits'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":314528,"url":"https://<example>.rossum.app/api/v1/suggested_edits/314528","annotation":"https://<example>.rossum.app/api/v1/annotations/314528","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314554","rotation":0},{"page":"https://<example>.rossum.app/api/v1/pages/314593","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}},{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314556","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528""values":{"edit:document_type":"invoice"}}]}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":314528,"url":"https://<example>.rossum.app/api/v1/suggested_edits/314528","annotation":"https://<example>.rossum.app/api/v1/annotations/314528","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314554","rotation":0},{"page":"https://<example>.rossum.app/api/v1/pages/314593","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}},{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314556","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528""values":{"edit:document_type":"invoice"}}]}]}
GET /v1/suggested_edits
GET /v1/suggested_edits
Retrieve all suggested edit objects.
Supported filters:annotation
annotation
Supported ordering:annotation
annotation
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofsuggested editobjects.

### Create a new suggested edit

Create new suggested_edit

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotation": "https://<example>.rossum.app/api/v1/annotations/123", "documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/123"}]}]}'\'https://<example>.rossum.app/api/v1/suggested_edits'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotation": "https://<example>.rossum.app/api/v1/annotations/123", "documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/123"}]}]}'\'https://<example>.rossum.app/api/v1/suggested_edits'

```
{"id":123,"url":"https://<example>.rossum.app/api/v1/suggested_edits/123","annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/123"}],"target_queue":"https://<example>.rossum.app/api/v1/queues/123","values":{}}]}
```

{"id":123,"url":"https://<example>.rossum.app/api/v1/suggested_edits/123","annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/123"}],"target_queue":"https://<example>.rossum.app/api/v1/queues/123","values":{}}]}
POST /v1/suggested_edits
POST /v1/suggested_edits
Create a new suggested edit object.

#### Response

Status:201
201
Returns createdsuggested editobject.

### Retrieve a suggested edit

Get suggested edit object558598
558598

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/suggested_edits/558598'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/suggested_edits/558598'

```
{"id":314528,"url":"https://<example>.rossum.app/api/v1/suggested_edits/314528","annotation":"https://<example>.rossum.app/api/v1/annotations/314528","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314554","rotation":0},{"page":"https://<example>.rossum.app/api/v1/pages/314593","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}},{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314556","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}}]}
```

{"id":314528,"url":"https://<example>.rossum.app/api/v1/suggested_edits/314528","annotation":"https://<example>.rossum.app/api/v1/annotations/314528","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314554","rotation":0},{"page":"https://<example>.rossum.app/api/v1/pages/314593","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}},{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314556","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}}]}
GET /v1/suggested_edits/{id}
GET /v1/suggested_edits/{id}
Get a suggested edit object.

#### Response

Status:200
200
Returnssuggested editobject.

### Update a suggested edit

Update suggested edit object1500
1500

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotation": "https://<example>.rossum.app/api/v1/annotations/1500", "documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/123"}]}]}'\'https://<example>.rossum.app/api/v1/suggested_edits/1500'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotation": "https://<example>.rossum.app/api/v1/annotations/1500", "documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/123"}]}]}'\'https://<example>.rossum.app/api/v1/suggested_edits/1500'

```
{"id":1500,"url":"https://<example>.rossum.app/api/v1/suggested_edits/1500","annotation":"https://<example>.rossum.app/api/v1/annotations/1500","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/123"}],"target_queue":"https://<example>.rossum.app/api/v1/queues/123","values":{}}]}
```

{"id":1500,"url":"https://<example>.rossum.app/api/v1/suggested_edits/1500","annotation":"https://<example>.rossum.app/api/v1/annotations/1500","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/123"}],"target_queue":"https://<example>.rossum.app/api/v1/queues/123","values":{}}]}
PUT /v1/suggested_edits/{id}
PUT /v1/suggested_edits/{id}
Update suggested edit object.

#### Response

Status:200
200
Returns updatedsuggested editobject.

### Update part of a suggested edit

Update documents on suggested edit object1500
1500

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/123"}]}]}'\'https://<example>.rossum.app/api/v1/suggested_edits/1500'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/123"}]}]}'\'https://<example>.rossum.app/api/v1/suggested_edits/1500'

```
{"id":1500,"url":"https://<example>.rossum.app/api/v1/suggested_edits/1500","annotation":"https://<example>.rossum.app/api/v1/annotations/1500","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/123"}],"target_queue":"https://<example>.rossum.app/api/v1/queues/123","values":{}}]}
```

{"id":1500,"url":"https://<example>.rossum.app/api/v1/suggested_edits/1500","annotation":"https://<example>.rossum.app/api/v1/annotations/1500","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/123"}],"target_queue":"https://<example>.rossum.app/api/v1/queues/123","values":{}}]}
PATCH /v1/suggested_edits/{id}
PATCH /v1/suggested_edits/{id}
Update part of suggested edit object.

#### Response

Status:200
200
Returns updatedsuggested editobject.

### Delete a suggested edit

Delete suggested edit1500
1500

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/suggested_edits/1500'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/suggested_edits/1500'
DELETE /v1/suggested_edits/{id}
DELETE /v1/suggested_edits/{id}
Delete suggested edit object.

#### Response

Status:204
204


## Survey

Example survey object

```
{"id":456,"url":"https://<example>.rossum.app/api/v1/surveys/456","organization":"https://<example>.rossum.app/api/v1/organizations/42","created_at":"2019-10-13T23:04:00.933658Z","modifier":"https://<example>.rossum.app/api/v1/users/100","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z","additional_data":{},"template":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","answers":[{"value":5,"question":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a"}]}
```

{"id":456,"url":"https://<example>.rossum.app/api/v1/surveys/456","organization":"https://<example>.rossum.app/api/v1/organizations/42","created_at":"2019-10-13T23:04:00.933658Z","modifier":"https://<example>.rossum.app/api/v1/users/100","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z","additional_data":{},"template":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","answers":[{"value":5,"question":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a"}]}
A Survey object represents a collection of answers and metadata related to the survey.
AttributeTypeDefaultDescriptionRead-onlyRequiredidintegerId of the surveytrueurlURLURL of the surveytrueorganizationURLRelated organizationtruetemplateURLRelated survey templatetruecreated_atdatetimeTimestamp of object's creation.truemodifierURLUser that last modified the annotation.truemodified_byURLUser that last modified the annotation.truemodified_atdatetimeTimestamp of last modification.trueadditional_dataobject{}Client data.answerslist[object]Answers, linked to the questions. The number of the answers can't be changed. Seeanswerstrue
{}

#### Answer

AttributeTypeDescriptionRead-onlyvalueJSONValue of the answer. The structure depends onquestion.answer_type. Seeanswer typequestionURLURL of the questiontrue
question.answer_type

#### Answer type

TypeDescriptionscaleInteger. Has to be in range 1-5.textString. Has to be at most 250 characters long.boolBoolean. Default isnull.
null

### List all surveys

List all surveys

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/surveys'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/surveys'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":234,"url":"https://<example>.rossum.app/api/v1/surveys/234",...}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":234,"url":"https://<example>.rossum.app/api/v1/surveys/234",...}]}
GET /v1/surveys
GET /v1/surveys
Retrieve all survey objects.
Supported filters:id,template_uuidSupported ordering:id,modified_at
id
template_uuid
id
modified_at
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofsurveyobjects.

### Create new survey object

Create new survey from template

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"uuid": "4d73ac4b-bd1a-4b6d-b274-4e976a382b5b"}'\'https://<example>.rossum.app/api/v1/surveys/from_template'
```

curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"uuid": "4d73ac4b-bd1a-4b6d-b274-4e976a382b5b"}'\'https://<example>.rossum.app/api/v1/surveys/from_template'

```
{"id":234,"url":"https://<example>.rossum.app/api/v1/surveys/234","template":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","answers":[{"value":null,"question":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a"}],...}
```

{"id":234,"url":"https://<example>.rossum.app/api/v1/surveys/234","template":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","answers":[{"value":null,"question":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a"}],...}
POST /v1/surveys/from_template
POST /v1/surveys/from_template
Create new survey object. Will have all answers pre-filled withnullanswers.
null

#### Response

Status:201
201
Returns newsurveyobject.

### Retrieve a survey object

Get survey object1234
1234

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/surveys/1234'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/surveys/1234'

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/surveys/1234",...}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/surveys/1234",...}
GET /v1/surveys/{id}
GET /v1/surveys/{id}
Get a survey object.

#### Response

Status:200
200
Returnssurveyobject.

### Update a survey

Update survey object1234
1234

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"additional_data": {"data": "some data"}, "answers": [{"value": 5}, {"value": 3}]}'\'https://<example>.rossum.app/api/v1/surveys/1234'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"additional_data": {"data": "some data"}, "answers": [{"value": 5}, {"value": 3}]}'\'https://<example>.rossum.app/api/v1/surveys/1234'

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/surveys/1234",...}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/surveys/1234",...}
PUT /v1/surveys/{id}
PUT /v1/surveys/{id}
Update survey object.

#### Response

Status:200
200
Returns updatedsurveyobject.

### Update part of a survey

Update subject of survey object1234
1234

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"additional_data": {"data": "some data"}, "answers": [{}, {"value": 3}, {}]}'\'https://<example>.rossum.app/api/v1/surveys/1234'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"additional_data": {"data": "some data"}, "answers": [{}, {"value": 3}, {}]}'\'https://<example>.rossum.app/api/v1/surveys/1234'

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/surveys/1234",...}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/surveys/1234",...}
PATCH /v1/surveys/{id}
PATCH /v1/surveys/{id}
Update part of a survey object. Empty answer object will not update contents of that answer.

#### Response

Status:200
200
Returns updatedsurveyobject.

### Delete a survey

Delete survey object1234
1234

```
curl-XDELETE'https://<example>.rossum.app/api/v1/surveys/1234'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
```

curl-XDELETE'https://<example>.rossum.app/api/v1/surveys/1234'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
DELETE /v1/surveys/{id}
DELETE /v1/surveys/{id}
Delete a survey object.

#### Response

Status:204
204


## Survey template

Example survey template object

```
{"url":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","uuid":"4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","name":"Satisfaction survey","questions":[{"uuid":"9e87fcf2-f571-4691-8850-77f813d6861a","text":"How satisfied are you?","answer_type":"scale"}]}
```

{"url":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","uuid":"4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","name":"Satisfaction survey","questions":[{"uuid":"9e87fcf2-f571-4691-8850-77f813d6861a","text":"How satisfied are you?","answer_type":"scale"}]}
A Survey template object represents a collection of questions related to asurvey.
AttributeTypeDescriptionuuidstringUUID of the survey templateurlURLURL of the survey templatenamestringName of the survey templatequestionslist[object]list of question objects

### List all survey templates

List all survey templates

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/survey_templates'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/survey_templates'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b",...}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b",...}]}
GET /v1/survey_templates
GET /v1/survey_templates
Retrieve all survey template objects.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofsurvey templateobjects.

### Retrieve a survey template

Get survey template object4d73ac4b-bd1a-4b6d-b274-4e976a382b5b
4d73ac4b-bd1a-4b6d-b274-4e976a382b5b

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b'

```
{"url":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b",...}
```

{"url":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b",...}
GET /v1/survey_templates/{uuid}
GET /v1/survey_templates/{uuid}
Get a survey template object.

#### Response

Status:200
200
Returnssurvey templateobject.


## Task

Example task object

```
{"id":1,"url":"https://<example>.rossum.app/api/v1/tasks/1","type":"documents_download","status":"succeeded","expires_at":"2021-09-11T09:59:00.000000Z","detail":null,"content":{"file_name":"my-archive.zip"},"result_url":"https://<example>.rossum.app/api/v1/documents/downloads/1"}
```

{"id":1,"url":"https://<example>.rossum.app/api/v1/tasks/1","type":"documents_download","status":"succeeded","expires_at":"2021-09-11T09:59:00.000000Z","detail":null,"content":{"file_name":"my-archive.zip"},"result_url":"https://<example>.rossum.app/api/v1/documents/downloads/1"}
Tasks are used as status monitors of asynchronous operations.
Tasks withsucceededstatus can redirect to the object created as a result of them. Ifno_redirect=trueis passed
as a query parameter, endpoint won't redirect to an object created, but will return information about the task itself instead.
succeeded
no_redirect=true
AttributeTypeOptionalDescriptionidintegerTask object ID.urlURLTask object URL.typeenumCurrently supported options for task types aredocuments_download,upload_created, andemail_imported.statusenumOne ofrunning,succeededorfailed.expires_atdatetimeTimestamp of a guaranteed availability of the task object. Expired tasks are being deleted periodically.detailstringDetailed message on the status of the task. For failed tasks, error id is included in the message and can be used in communication with Rossum support for further investigation.contentobjectDetailed information related to tasks (seetasks contentdetail).codestringtrueError code.result_urlstringtrueSucceeded status resulting redirect URL.
documents_download
upload_created
email_imported
running
succeeded
failed

#### Tasks content

Contains detailed information related to tasks.
AttributeTypeOptionalDescriptionfile_namestringFile name of the archive to be downloaded specified when creating adownload.
AttributeTypeDescriptionuploadurlURL of the object representing theupload.

### Retrieve task

Get task24
24

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/tasks/24'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/tasks/24'

```
{"id":24,"url":"https://<example>.rossum.app/api/v1/tasks/24","type":"documents_download","status":"running","expires_at":"2021-09-11T09:59:00.000000Z","detail":null,"content":{"file_name":"my-archive.zip"}}
```

{"id":24,"url":"https://<example>.rossum.app/api/v1/tasks/24","type":"documents_download","status":"running","expires_at":"2021-09-11T09:59:00.000000Z","detail":null,"content":{"file_name":"my-archive.zip"}}
GET /v1/tasks/{id}
GET /v1/tasks/{id}

#### Response

Status:200or303
200
303
If the task has status other thansucceeded, the endpoint returns status200.
If the task has statussucceeded, the endpoint redirects with status303to the newly created object.
Ifno_redirectflag was passed, the endpoint returns the task object and status200.
succeeded
200
succeeded
303
no_redirect
200
Returnstaskobject.


## Trigger

Example trigger object

```
{"id":234,"url":"https://<example>.rossum.app/api/v1/triggers/234","queue":"https://<example>.rossum.app/api/v1/queues/4321","event":"annotation_imported","condition":{},"email_templates":["https://<example>.rossum.app/api/v1/email_templates/123","https://<example>.rossum.app/api/v1/email_templates/321"],"delete_recommendations":["https://<example>.rossum.app/api/v1/delete_recommendations/123","https://<example>.rossum.app/api/v1/delete_recommendations/321"]}
```

{"id":234,"url":"https://<example>.rossum.app/api/v1/triggers/234","queue":"https://<example>.rossum.app/api/v1/queues/4321","event":"annotation_imported","condition":{},"email_templates":["https://<example>.rossum.app/api/v1/email_templates/123","https://<example>.rossum.app/api/v1/email_templates/321"],"delete_recommendations":["https://<example>.rossum.app/api/v1/delete_recommendations/123","https://<example>.rossum.app/api/v1/delete_recommendations/321"]}
A Trigger object represents a condition that will trigger its related object's actions when an event occurs.
AttributeTypeDefaultRequiredDescriptionRead-onlyidintegerId of the triggertrueurlURLURL of the triggertruequeueURLtrueURL of the associated queueeventstringtrueEvent that will trigger the trigger (seetrigger event types)conditionJSON{}A subset of MongoDB Query Language (seetrigger condition)email_templateslist[URL]URLs of the linked email templatesdelete_recommendationslist[URL]URLs of the linked delete recommendations
Detailed information on how to set up and use Triggers can be foundhere.
email_with_no_processable_attachments

### List all triggers

List all triggers

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/triggers'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/triggers'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":234,"url":"https://<example>.rossum.app/api/v1/triggers/234",...}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":234,"url":"https://<example>.rossum.app/api/v1/triggers/234",...}]}
GET /v1/triggers
GET /v1/triggers
Retrieve all trigger objects.
Supported filters:id,event,queueSupported ordering:id,event
id
event
queue
id
event
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list oftriggerobjects.

### Create new trigger object

Create new trigger in queue4321
4321

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "event": "annotation_created", "condition": {}}'\'https://<example>.rossum.app/api/v1/triggers'
```

curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "event": "annotation_created", "condition": {}}'\'https://<example>.rossum.app/api/v1/triggers'

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/triggers/1234","queue":"https://<example>.rossum.app/api/v1/queues/4321","event":"annotation_created","condition":{}}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/triggers/1234","queue":"https://<example>.rossum.app/api/v1/queues/4321","event":"annotation_created","condition":{}}
POST /v1/triggers
POST /v1/triggers
Create new trigger object.

#### Response

Status:201
201
Returns newtriggerobject.

### Retrieve a trigger object

Get trigger object1234
1234

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/triggers/1234'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/triggers/1234'

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/triggers/1234",...}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/triggers/1234",...}
GET /v1/triggers/{id}
GET /v1/triggers/{id}
Get a trigger object.

#### Response

Status:200
200
Returnstriggerobject.

### Update a trigger

Update trigger object1234
1234

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "event": "annotation_created", "condition": {}}'\'https://<example>.rossum.app/api/v1/triggers/1234'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "event": "annotation_created", "condition": {}}'\'https://<example>.rossum.app/api/v1/triggers/1234'

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/triggers/1234",...}
```

{"id":1234,"url":"https://<example>.rossum.app/api/v1/triggers/1234",...}
PUT /v1/triggers/{id}
PUT /v1/triggers/{id}
Update trigger object.

#### Response

Status:200
200
Returns updatedtriggerobject.

### Update part of a trigger

Update subject of trigger object1234
1234

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"event": "annotation_imported"}'\'https://<example>.rossum.app/api/v1/triggers/1234'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"event": "annotation_imported"}'\'https://<example>.rossum.app/api/v1/triggers/1234'

```
{"id":1234,"event":"annotation_imported",...}
```

{"id":1234,"event":"annotation_imported",...}
PATCH /v1/triggers/{id}
PATCH /v1/triggers/{id}
Update part of a trigger object.

#### Response

Status:200
200
Returns updatedtriggerobject.

### Delete a trigger

Delete trigger object1234
1234

```
curl-XDELETE'https://<example>.rossum.app/api/v1/triggers/1234'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
```

curl-XDELETE'https://<example>.rossum.app/api/v1/triggers/1234'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
DELETE /v1/triggers/{id}
DELETE /v1/triggers/{id}
Delete a trigger object.
Trigger ofemail_with_no_processable_attachmentseventcannot be deleted.
email_with_no_processable_attachments

#### Response

Status:204
204


## Upload

Example upload object

```
{"id":314528,"url":"https://<example>.rossum.app/api/v1/uploads/314528","queue":"https://<example>.rossum.app/api/v1/queues/8199","creator":"https://<example>.rossum.app/api/v1/users/1","created_at":"2021-04-26T10:08:03.856648Z","email":"https://<example>.rossum.app/api/v1/emails/96743","organization":"https://<example>.rossum.app/api/v1/organizations/1","documents":["https://<example>.rossum.app/api/v1/documents/254322","https://<example>.rossum.app/api/v1/documents/254323"],"additional_documents":["https://<example>.rossum.app/api/v1/documents/254324"],"annotations":["https://<example>.rossum.app/api/v1/annotations/104322","https://<example>.rossum.app/api/v1/annotations/104323","https://<example>.rossum.app/api/v1/annotations/104324"]}
```

{"id":314528,"url":"https://<example>.rossum.app/api/v1/uploads/314528","queue":"https://<example>.rossum.app/api/v1/queues/8199","creator":"https://<example>.rossum.app/api/v1/users/1","created_at":"2021-04-26T10:08:03.856648Z","email":"https://<example>.rossum.app/api/v1/emails/96743","organization":"https://<example>.rossum.app/api/v1/organizations/1","documents":["https://<example>.rossum.app/api/v1/documents/254322","https://<example>.rossum.app/api/v1/documents/254323"],"additional_documents":["https://<example>.rossum.app/api/v1/documents/254324"],"annotations":["https://<example>.rossum.app/api/v1/annotations/104322","https://<example>.rossum.app/api/v1/annotations/104323","https://<example>.rossum.app/api/v1/annotations/104324"]}
Object representing an upload.
AttributeTypeOptionalDescriptionurlURLUpload object URL.queueURLURL of the target queue of the upload.emailURLtrueURL of the email that created the upload object (if applicable).organizationURLURL of related organizationcreatorURLURL of the user who created the upload.created_atdatetimeTime of the creation of the upload.documentslist[URL]URLs of the uploaded documents.additional_documentslist[URL]trueURLs of additional documents created inupload.createdevent hooks.annotationslist[URL]trueURLs of all created annotations.
upload.created

### Create upload

Upload file using a form (multipart/form-data)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
Upload file in a request body

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
Upload file in a request body (UTF-8 filename must be URL encoded)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H"Content-Disposition: attachment; filename*=utf-8''document%20%F0%9F%8E%81.pdf"--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H"Content-Disposition: attachment; filename*=utf-8''document%20%F0%9F%8E%81.pdf"--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
Upload file in a request body with a filename in URL (UTF-8 filename must be URL encoded)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads/document%20%F0%9F%8E%81.pdf?queue=8236'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads/document%20%F0%9F%8E%81.pdf?queue=8236'
Upload multiple files using multipart/form-data

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document1.pdf-Fcontent=@document2.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document1.pdf-Fcontent=@document2.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
Upload file using basic authentication

```
curl-u'east-west-trading-co@<example>.rossum.app:secret'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

curl-u'east-west-trading-co@<example>.rossum.app:secret'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
Upload file with additional field values and metadata

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\-Fvalues='{"upload:organization_unit":"Sales"}'\-Fmetadata='{"project":"Market ABC"}'\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\-Fvalues='{"upload:organization_unit":"Sales"}'\-Fmetadata='{"project":"Market ABC"}'\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
POST /v1/uploads?queue={id}
POST /v1/uploads?queue={id}
POST /v1/uploads/{filename}?queue={id}
POST /v1/uploads/{filename}?queue={id}
Uploads a document to the queue specified as query parameter (starting in theimporting state).
Multiple files upload is supported, the total size of the data uploaded may not exceed 40 MB.
UTF-8 filenames are supported, see examples.
The file can be sent as a part of multipart/form-data or, alternatively, in the
request body.
The{filename}parameter in the URL path only works when sending the file in the request body using--data-binary.
When uploading via multipart/form-data, the filename is automatically extracted from the form field and the{filename}parameter in the URL is ignored. Use theContent-Dispositionheader or specify the filename in the form field instead.
{filename}
--data-binary
{filename}
Content-Disposition
You can also specify additional properties using form field:
- metadata could be passed usingmetadataform field. Metadata will
be set to newly created annotation object.
metadata
- values could be passed usingvaluesform field. It may
be used to initialize datapoint values by setting the value ofrir_field_namesin the schema.
values
rir_field_names
For exampleupload:organization_unitfield may be referenced in a schema like this:{
     "category": "datapoint",
     "id": "organization_unit",
     "label": "Org unit",
     "type": "string",
     "rir_field_names": ["upload:organization_unit"]
     ...
   }
upload:organization_unit

```
{
     "category": "datapoint",
     "id": "organization_unit",
     "label": "Org unit",
     "type": "string",
     "rir_field_names": ["upload:organization_unit"]
     ...
   }
```

Upload endpoint also supportsbasic authenticationto enable easy integration
with third-party systems.
Fail upload if a document with identical content andoriginal_file_namealready exists.
original_file_name

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236&reject_identical=true'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236&reject_identical=true'
Additional arguments may be specified to prevent reupload of identical documents.
This is useful for various services and integrations that track uploaded
documents. In case of failure or service restart, the current progress may be
lost and reupload of the previously uploaded document may happen. Usingreject_identicalargument prevents such duplicates.
reject_identical
ArgumentTypeDefaultDescriptionreject_identicalbooleanfalseWhen enabled, upload checks for identical documents within a given organization. If such document is found, upload fails with status 409. The check is performed based on file name and file content. Only one file is allowed whenreject_identicalis set totrue.
reject_identical
reject_identical
true

#### Response

Status:202
202
Create upload endpoint is asynchronous and response contains created task url. Further information about
the import status may be acquired by retrieving the upload object or the task (for more information, please refer totask)
Example import response

```
{
  "url": "https://example.rossum.app/api/v1/tasks/315509"
}
```


### Retrieve upload

Get upload314528
314528

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/uploads/314528'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/uploads/314528'

```
{"id":314528,"url":"https://<example>.rossum.app/api/v1/uploads/314528","queue":"https://<example>.rossum.app/api/v1/queues/8199","creator":"https://<example>.rossum.app/api/v1/users/1","created_at":"2021-04-26T10:08:03.856648Z","email":"https://<example>.rossum.app/api/v1/emails/96743","organization":"https://<example>.rossum.app/api/v1/organizations/1","documents":["https://<example>.rossum.app/api/v1/documents/254322","https://<example>.rossum.app/api/v1/documents/254323"],"additional_documents":["https://<example>.rossum.app/api/v1/documents/254324"],"annotations":["https://<example>.rossum.app/api/v1/annotations/104322","https://<example>.rossum.app/api/v1/annotations/104323","https://<example>.rossum.app/api/v1/annotations/104324"]}
```

{"id":314528,"url":"https://<example>.rossum.app/api/v1/uploads/314528","queue":"https://<example>.rossum.app/api/v1/queues/8199","creator":"https://<example>.rossum.app/api/v1/users/1","created_at":"2021-04-26T10:08:03.856648Z","email":"https://<example>.rossum.app/api/v1/emails/96743","organization":"https://<example>.rossum.app/api/v1/organizations/1","documents":["https://<example>.rossum.app/api/v1/documents/254322","https://<example>.rossum.app/api/v1/documents/254323"],"additional_documents":["https://<example>.rossum.app/api/v1/documents/254324"],"annotations":["https://<example>.rossum.app/api/v1/annotations/104322","https://<example>.rossum.app/api/v1/annotations/104323","https://<example>.rossum.app/api/v1/annotations/104324"]}
GET /v1/uploads/{id}
GET /v1/uploads/{id}

#### Response

Status:200
200
Returnsuploadobject.


## User

Example user object

```
{"id":10775,"url":"https://<example>.rossum.app/api/v1/users/10775","first_name":"John","last_name":"Doe","email":"john-doe@east-west-trading.com","phone_number":"+1-212-456-7890","date_joined":"2018-09-19T13:44:56.000000Z","username":"john-doe@east-west-trading.com","groups":["https://<example>.rossum.app/api/v1/groups/3"],"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"is_active":true,"last_login":"2019-02-07T16:20:18.652253Z","ui_settings":{},"metadata":{},"oidc_id":null,"deleted":false}
```

{"id":10775,"url":"https://<example>.rossum.app/api/v1/users/10775","first_name":"John","last_name":"Doe","email":"john-doe@east-west-trading.com","phone_number":"+1-212-456-7890","date_joined":"2018-09-19T13:44:56.000000Z","username":"john-doe@east-west-trading.com","groups":["https://<example>.rossum.app/api/v1/groups/3"],"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"is_active":true,"last_login":"2019-02-07T16:20:18.652253Z","ui_settings":{},"metadata":{},"oidc_id":null,"deleted":false}
A user object represents individual user of Rossum. Every user is assigned to an organization.
A user can be assigneduser roles(permission groups). User usually has only one assigned role (with the exception ofapproverrole).
User may be assigned to one or more queues and can only access annotations
from the assigned queues. This restriction is not applied to admin users, who may
access annotations from all queues.
Users cannot be deleted, but can be disabled (setis_activetofalse).
Fieldemailcannot be changed through the API (due to security reasons).
Fieldpasswordcan be set onuser creationbut cannot be changed through the API (due to security reasons).
Fieldoidc_idwill be set to User's email when transitioning tossoauthorization, if empty.
is_active
false
email
password
oidc_id
sso
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the usertrueurlURLURL of the usertruefirst_namestringFirst name of the userlast_namestringLast name of the useremailstringEmail of the usertruephone_numberstringPhone number of the userpasswordstringPassword (not shown on API)date_joineddatetimeDate of user joinusernamestringUsername of a usergroupslist[URL][]List ofuser role(permission groups)organizationURLRelated organization.queueslist[URL][]List of queues user is assigned to.is_activebooltrueWhether user is enabled or disabledlast_logindatetimeDate of last loginui_settingsobject{}User-related frontend UI settings (e.g. locales). Rossum internal.metadataobject{}Client data.oidc_idstringnullOIDC provider id used to match Rossum user (displayed only to admin user)auth_typestringpasswordAuthorization method, can bessoorpassword. This field can be edited only by admin.deletedboolfalseWhether a user is deletedtrue
[]
[]
true
{}
{}
password
sso
password
false

### List all users

List all users in the organization.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/users'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/users'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":10775,"url":"https://<example>.rossum.app/api/v1/users/10775","first_name":"John","last_name":"Doe","email":"john-doe@east-west-trading.com","date_joined":"2018-09-19T13:44:56.000000Z","username":"john-doe@east-west-trading.com",...}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":10775,"url":"https://<example>.rossum.app/api/v1/users/10775","first_name":"John","last_name":"Doe","email":"john-doe@east-west-trading.com","date_joined":"2018-09-19T13:44:56.000000Z","username":"john-doe@east-west-trading.com",...}]}
GET /v1/users
GET /v1/users
Retrieve all user objects.
Supported filters:id,organization,username,first_name,last_name,email,is_active,last_login,groups,queue,deleted
id
organization
username
first_name
last_name
email
is_active
last_login
groups
queue
deleted
Supported ordering:id,username,first_name,last_name,email,last_login,date_joined,deleted,not_deleted
id
username
first_name
last_name
email
last_login
date_joined
deleted
not_deleted
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofuserobjects.

### Create new user

Create new user in organization406
406

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406", "username": "jane@east-west-trading.com", "email": "jane@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"], "groups": ["https://<example>.rossum.app/api/v1/groups/2"]}'\'https://<example>.rossum.app/api/v1/users'
```

curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406", "username": "jane@east-west-trading.com", "email": "jane@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"], "groups": ["https://<example>.rossum.app/api/v1/groups/2"]}'\'https://<example>.rossum.app/api/v1/users'

```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"","last_name":"","email":"jane@east-west-trading.com","date_joined":"2019-02-09T22:16:38.969904Z","username":"jane@east-west-trading.com","phone_number":null,"groups":["https://<example>.rossum.app/api/v1/groups/2"],"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"is_active":true,"last_login":null,"ui_settings":{},"metadata":{},"oidc_id":null,"deleted":false}
```

{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"","last_name":"","email":"jane@east-west-trading.com","date_joined":"2019-02-09T22:16:38.969904Z","username":"jane@east-west-trading.com","phone_number":null,"groups":["https://<example>.rossum.app/api/v1/groups/2"],"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"is_active":true,"last_login":null,"ui_settings":{},"metadata":{},"oidc_id":null,"deleted":false}
Create a new user with password and no email (a technical user)

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406", "username": "technical-user@east-west-trading.com", "password": "secret"}'\'https://<example>.rossum.app/api/v1/users'
```

curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406", "username": "technical-user@east-west-trading.com", "password": "secret"}'\'https://<example>.rossum.app/api/v1/users'

```
{"id":10998,"url":"https://<example>.rossum.app/api/v1/users/10998","first_name":"","last_name":"","email":"","date_joined":"2020-09-25T14:30:38.969904Z","username":"technical-user@east-west-trading.com","groups":[],"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"is_active":true,"last_login":null,"ui_settings":{},"metadata":{},"oidc_id":null,"deleted":false,...}
```

{"id":10998,"url":"https://<example>.rossum.app/api/v1/users/10998","first_name":"","last_name":"","email":"","date_joined":"2020-09-25T14:30:38.969904Z","username":"technical-user@east-west-trading.com","groups":[],"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"is_active":true,"last_login":null,"ui_settings":{},"metadata":{},"oidc_id":null,"deleted":false,...}
POST /v1/users
POST /v1/users
Create a new user object.For security reasons, it is better to create users without a specified password.
Such users have an invalid password.
Later, they can set their password after usingreset-password endpoint.

#### Response

Status:201
201
Returns createduserobject.

### Retrieve a user

Get user object10997
10997

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/users/10997'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/users/10997'

```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Jane","last_name":"Bond","email":"jane@east-west-trading.com","date_joined":"2019-02-09T22:16:38.969904Z","username":"jane@east-west-trading.com",...}
```

{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Jane","last_name":"Bond","email":"jane@east-west-trading.com","date_joined":"2019-02-09T22:16:38.969904Z","username":"jane@east-west-trading.com",...}
GET /v1/users/{id}
GET /v1/users/{id}
Get a user object.

#### Response

Status:200
200
Returnsuserobject.

### Retrieve currently authorized user

Get user object for the currently authorized user

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/auth/user'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/auth/user'

```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Jane","last_name":"Bond","email":"jane@east-west-trading.com","date_joined":"2019-02-09T22:16:38.969904Z","username":"jane@east-west-trading.com",...}
```

{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Jane","last_name":"Bond","email":"jane@east-west-trading.com","date_joined":"2019-02-09T22:16:38.969904Z","username":"jane@east-west-trading.com",...}
GET /v1/auth/user
GET /v1/auth/user
Get user object for the currently authorized user.

#### Response

Status:200
200
Returnsuserobject.

### Update a user

Update user object10997
10997

```
curl-s-XPUT-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406", "username": "jane@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"], "groups": ["https://<example>.rossum.app/api/v1/groups/2"], "first_name": "Jane"}'\'https://<example>.rossum.app/api/v1/users/10997'
```

curl-s-XPUT-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406", "username": "jane@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"], "groups": ["https://<example>.rossum.app/api/v1/groups/2"], "first_name": "Jane"}'\'https://<example>.rossum.app/api/v1/users/10997'

```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Jane","last_name":"","email":"jane@east-west-trading.com",...}
```

{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Jane","last_name":"","email":"jane@east-west-trading.com",...}
PUT /v1/users/{id}
PUT /v1/users/{id}
Update user object.

#### Response

Status:200
200
Returns updateduserobject.

### Update part of a user

Updatefirst_nameof user object10997
first_name
10997

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"first_name": "Emma"}'\'https://<example>.rossum.app/api/v1/users/10997'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"first_name": "Emma"}'\'https://<example>.rossum.app/api/v1/users/10997'

```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Emma","last_name":"",...}
```

{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Emma","last_name":"",...}
PATCH /v1/users/{id}
PATCH /v1/users/{id}
Update part of user object.

#### Response

Status:200
200
Returns updateduserobject.

### Deleting a user

The following endpoints provide soft-deletion - marking a user as deleted, without a possibility of reversing the deletion.
The following rules apply to user soft-deletion:
- A regular user can delete self and nobody else
A regular user can delete self and nobody else
- An organization admin can delete other users within the organization, including other adminsFor trial organizations, the admin deleting self actually means the whole trial organization will be deletedFor non-trial organizationThe last admin cannot be deleted via API, but must instead create a ticket with supportIf the organization has an organization group admin, the admin can delete self but the org will be preserved
An organization admin can delete other users within the organization, including other admins
- For trial organizations, the admin deleting self actually means the whole trial organization will be deleted
- For non-trial organization
- The last admin cannot be deleted via API, but must instead create a ticket with support
- If the organization has an organization group admin, the admin can delete self but the org will be preserved
- An organization group adminCannot be deleted via APICan remove any organization admin or regular user
An organization group admin
- Cannot be deleted via API
- Can remove any organization admin or regular user

#### Soft-deletion

Delete user1337
1337

```
curl-XDELETE-H'Authorization: token db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/users/1337'
```

curl-XDELETE-H'Authorization: token db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/users/1337'
DELETE /v1/users/{id}
DELETE /v1/users/{id}

#### Response

Status:204
204

### Password

Due to security reasons, user passwords cannot be set directly using the standard CRUD operations.
Instead, the following endpoints can be used for resetting and changing passwords.
Password requirements:
- Length: 12–64 characters
- May not be similar to username
- May not contain common words
- May not be numeric only
- Must pass complexity check

#### Change password

Change password of user object10997
10997

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"new_password1": "new_password", "new_password2": "new_password", "old_password": "old_password"}'\'https://<example>.rossum.app/api/v1/auth/password/change'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"new_password1": "new_password", "new_password2": "new_password", "old_password": "old_password"}'\'https://<example>.rossum.app/api/v1/auth/password/change'

```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997",...}
```

{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997",...}
POST /v1/auth/password/change
POST /v1/auth/password/change
Change password of current user.

#### Response

Status:200
200
Returnsuserobject.

#### Reset password

Reset password of a user with emailjane@east-west-trading.com
jane@east-west-trading.com

```
curl-XPOST-H'Content-Type: application/json'\-d'{"email": "jane@east-west-trading.com"}'\'https://<example>.rossum.app/api/v1/auth/password/reset'
```

curl-XPOST-H'Content-Type: application/json'\-d'{"email": "jane@east-west-trading.com"}'\'https://<example>.rossum.app/api/v1/auth/password/reset'

```
{"detail":"Password reset e-mail has been sent."}
```

{"detail":"Password reset e-mail has been sent."}
POST /v1/auth/password/reset
POST /v1/auth/password/reset
Reset password to a users specified by their emails.
The users are sent an email with a verification URL leading to web form, where they can set their password.

#### Response

Status:200
200

#### Password score

Password score and suggestions from the validators.

```
curl-XPOST-H'Content-Type: application/json'\-d'{"password": "password_to_score"}'\'https://<example>.rossum.app/api/v1/auth/password/score'
```

curl-XPOST-H'Content-Type: application/json'\-d'{"password": "password_to_score"}'\'https://<example>.rossum.app/api/v1/auth/password/score'

```
{"score":2,"messages":["Add another word or two. Uncommon words are better."]}
```

{"score":2,"messages":["Add another word or two. Uncommon words are better."]}
POST /v1/auth/password/score
POST /v1/auth/password/score
Score to allow users to see how strong their password is from 0 (risky password) to 4 (strong password).
AttributeTypeDescriptionRequiredpasswordstringPassword to be scoredYesemailstringEmail of the userNofirst_namestringFirst name of the userNolast_namestringLast name of the userNo

#### Response

Status:200
200


## User Role

Example role object

```
{"id":3,"url":"https://<example>.rossum.app/api/v1/groups/3","name":"admin"}
```

{"id":3,"url":"https://<example>.rossum.app/api/v1/groups/3","name":"admin"}
User role is a group of permissions that are assigned to the user. Permissions
are assigned to individual operations on objects.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the user role (may differ between different organizations)trueurlURLURL of the user roletruenamestringName of the user roletrue
There are multiple pre-defined roles:
RoleDescriptionviewerRead-only user, cannot change any API object. May be useful for automated data export or auditor access.annotatorIn addition to permissions of annotator_limited the user is also allowed toimport a document.adminUser can modify API objects to set-up organization (e.g.workspaces,queues,schemas)managerIn addition to permissions of annotator the user is also allowed to accessusage-reports.annotator_limitedUser that is allowed to change annotation and its datapoints. Note: this role is under active development and should not be used in production environment.annotator_embeddedThis role is specifically designed to be used withembedded mode. User can modify annotation and its datapoints, also has read-only permissions for objects needed for interaction on embedded validation screen.organization_group_adminIn addition to permissions of admin the user can managemembershipsamongorganizationswithin herorganization group.Talk with a Rossum representative about enabling this feature.approverIn addition to permission of viewer the user can also approve/reject annotations. This may be combined with other roles.Talk with a Rossum representative about enabling this feature.For more info seeworkflows.
User can only access annotations from queues it is assigned to, except foradminandorganization_group_adminroles that can access any queue.
admin
organization_group_admin
Permissions assigned to the role cannot be changed through the API.

### List all user roles

List all user roles (groups)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/groups'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/groups'

```
{"pagination":{"total":6,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/groups/1","name":"viewer"},{"id":2,"url":"https://<example>.rossum.app/api/v1/groups/2","name":"annotator"},{"id":3,"url":"https://<example>.rossum.app/api/v1/groups/3","name":"admin"},{"id":4,"url":"https://<example>.rossum.app/api/v1/groups/4","name":"manager"},{"id":5,"url":"https://<example>.rossum.app/api/v1/groups/5","name":"annotator_limited"},{"id":6,"url":"https://<example>.rossum.app/api/v1/groups/6","name":"organization_group_admin"},{"id":7,"url":"https://<example>.rossum.app/api/v1/groups/7","name":"approver"}]}
```

{"pagination":{"total":6,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/groups/1","name":"viewer"},{"id":2,"url":"https://<example>.rossum.app/api/v1/groups/2","name":"annotator"},{"id":3,"url":"https://<example>.rossum.app/api/v1/groups/3","name":"admin"},{"id":4,"url":"https://<example>.rossum.app/api/v1/groups/4","name":"manager"},{"id":5,"url":"https://<example>.rossum.app/api/v1/groups/5","name":"annotator_limited"},{"id":6,"url":"https://<example>.rossum.app/api/v1/groups/6","name":"organization_group_admin"},{"id":7,"url":"https://<example>.rossum.app/api/v1/groups/7","name":"approver"}]}
GET /v1/groups
GET /v1/groups
Retrieve all group objects.
Supported filters:name
name
Supported ordering:name
name
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofgroupobjects.

### Retrieve a user role

Get group object2
2

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/groups/2'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/groups/2'

```
{"url":"https://<example>.rossum.app/api/v1/groups/2","name":"annotator"}
```

{"url":"https://<example>.rossum.app/api/v1/groups/2","name":"annotator"}
GET /v1/groups/{id}
GET /v1/groups/{id}
Get a user role object.

#### Response

Status:200
200
Returnsgroupobject.


## Webhook

webhook
webhook
hook
hook


## Workflow

Example workflow object

```
{"id":7540,"name":"Approval workflow for US entity","url":"https://<example>.rossum.app/api/v1/workflows/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","condition":{}}
```

{"id":7540,"name":"Approval workflow for US entity","url":"https://<example>.rossum.app/api/v1/workflows/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","condition":{}}
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the workflowtruenamestringName of the workflowurlURLURL of the workflowtrueorganizationURLURL of the organizationconditionJSONCondition that designates whether the workflow will be entered

### List all workflows

List all workflows

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflows'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflows'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"name":"Approval workflow for US entity","url":"https://<example>.rossum.app/api/v1/workflows/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","condition":{}}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"name":"Approval workflow for US entity","url":"https://<example>.rossum.app/api/v1/workflows/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","condition":{}}]}
GET /v1/workflows
GET /v1/workflows
Retrieve all workflow objects.
Supported filters:id,queue
id
queue
Supported ordering:id
id
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofworkflowobjects.

### Retrieve a workflow

Get workflow object7694
7694

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflows/7694'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflows/7694'

```
{"id":7540,"name":"Approval workflow for US entity","url":"https://<example>.rossum.app/api/v1/workflows/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","condition":{}}
```

{"id":7540,"name":"Approval workflow for US entity","url":"https://<example>.rossum.app/api/v1/workflows/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","condition":{}}
GET /v1/workflows/{id}
GET /v1/workflows/{id}
Get a workflow object.

#### Response

Status:200
200
Returnsworkflowobject.


## Workflow activity

Example workflow activity object

```
{"id":7540,"url":"https://<example>.rossum.app/api/v1/workflow_activities/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","created_by":null,"created_at":"2021-04-26T10:08:03.856648Z","annotation":"https://<example>.rossum.app/api/v1/annotations/406101","workflow":"https://<example>.rossum.app/api/v1/workflows/7540","workflow_step":"https://<example>.rossum.app/api/v1/workflow_steps/75","workflow_run":"https://<example>.rossum.app/api/v1/workflow_runs/7512","assignees":["https://<example>.rossum.app/api/v1/users/1","https://<example>.rossum.app/api/v1/users/2"],"action":"step_started","note":"The workflow step started"}
```

{"id":7540,"url":"https://<example>.rossum.app/api/v1/workflow_activities/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","created_by":null,"created_at":"2021-04-26T10:08:03.856648Z","annotation":"https://<example>.rossum.app/api/v1/annotations/406101","workflow":"https://<example>.rossum.app/api/v1/workflows/7540","workflow_step":"https://<example>.rossum.app/api/v1/workflow_steps/75","workflow_run":"https://<example>.rossum.app/api/v1/workflow_runs/7512","assignees":["https://<example>.rossum.app/api/v1/users/1","https://<example>.rossum.app/api/v1/users/2"],"action":"step_started","note":"The workflow step started"}
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the workflow activitytrueurlURLURL of the workflow activitytrueorganizationURLURL of the organizationtrueannotationURLURL of the related annotationtrueworkflowURLURL of the related workflowtrueworkflow stepURLURL of the related workflow steptrueworkflow runURLURL of the related workflow runtrueassigneeslist[URL]List of all assigneduserstrueactionstringSupported values arestep_started,step_completed,approved,rejected,workflow_started,workflow_completed,reassignedtruenotestringString note of the activitytruecreated_atdatetimeDate and time of when the activity was createdtruecreated_byURLnullUserwho created the activitytrue
step_started
step_completed
approved
rejected
workflow_started
workflow_completed
reassigned
null

### List all workflow activities

List all workflow activities

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_activities'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_activities'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"url":"https://<example>.rossum.app/api/v1/workflow_activities/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406",...}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"url":"https://<example>.rossum.app/api/v1/workflow_activities/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406",...}]}
GET /v1/workflow_activities
GET /v1/workflow_activities
Retrieve all workflow activity objects.
Supported filters:id,annotation,workflow_run,created_at_before,created_at_after,assignees,action
id
annotation
workflow_run
created_at_before
created_at_after
assignees
action
Supported ordering:id
id
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofworkflow activityobjects.

### Retrieve a workflow activity

Get workflow activity object7694
7694

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_activities/7540'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_activities/7540'

```
{"id":7540,"url":"https://<example>.rossum.app/api/v1/workflow_activities/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406",...}
```

{"id":7540,"url":"https://<example>.rossum.app/api/v1/workflow_activities/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406",...}
GET /v1/workflow_activities/{id}
GET /v1/workflow_activities/{id}
Get a workflow activity object.

#### Response

Status:200
200
Returnsworkflow activityobject.


## Workflow run

Example workflow run object

```
{"id":75402,"url":"https://<example>.rossum.app/api/v1/workflow_runs/75402","organization":"https://<example>.rossum.app/api/v1/organizations/406","annotation":"https://<example>.rossum.app/api/v1/annotations/7568","current_step":"https://<example>.rossum.app/api/v1/workflow_steps/7540","workflow_status":"pending"}
```

{"id":75402,"url":"https://<example>.rossum.app/api/v1/workflow_runs/75402","organization":"https://<example>.rossum.app/api/v1/organizations/406","annotation":"https://<example>.rossum.app/api/v1/annotations/7568","current_step":"https://<example>.rossum.app/api/v1/workflow_steps/7540","workflow_status":"pending"}
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the workflow runtrueurlURLURL of the workflow runtrueorganizationURLURL of the organizationtrueannotationURLURL of the annotationtruecurrent_stepURLURL of the workflow steptrueworkflow_statusstringpendingStatus of the workflow run (supported values:pending,approved,rejected)true
pending
pending
approved
rejected

### List all workflow runs

List all workflow runs

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_runs'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_runs'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":75402,"url":"https://<example>.rossum.app/api/v1/workflow_runs/75402",...}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":75402,"url":"https://<example>.rossum.app/api/v1/workflow_runs/75402",...}]}
GET /v1/workflow_runs
GET /v1/workflow_runs
Retrieve all workflow run objects.
Supported filters:id,annotation,current_step,workflow_status
id
annotation
current_step
workflow_status
Supported ordering:id
id
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofworkflow runsobjects.

### Retrieve a workflow run

Get workflow run object75402
75402

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_runs/75402'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_runs/75402'

```
{"id":75402,"url":"https://<example>.rossum.app/api/v1/workflow_runs/75402",...}
```

{"id":75402,"url":"https://<example>.rossum.app/api/v1/workflow_runs/75402",...}
GET /v1/workflow_runs/{id}
GET /v1/workflow_runs/{id}
Get a workflow run object.

#### Response

Status:200
200
Returnsworkflow runobject.

### Reset workflow run

Reset workflow run of ID319668
319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"note_content": "Resetting due to invalid due date."}'\'https://<example>.rossum.app/api/v1/workflow_runs/319668/reset'
```

curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"note_content": "Resetting due to invalid due date."}'\'https://<example>.rossum.app/api/v1/workflow_runs/319668/reset'
POST /v1/workflow_runs/{id}/reset
POST /v1/workflow_runs/{id}/reset
Resetting the workflow run leads to
- change its workflow status toin_review
in_review
- empty annotation'sassignees
assignees
- set the annotation status toto_review
to_review
- createworkflow activityof actionpushed_back
pushed_back
KeyDescriptionRequiredDefaultnote_contentString noteNo""
in_workflow

#### Response

Status:200
200
KeyTypeDescriptionannotation_statusstringNew status of the annotation (to_review).workflow_statusstringNew workflow status (in_review).
to_review
in_review


## Workflow step

Example workflow step object

```
{"id":7540,"name":"Team Lead approval step","url":"https://<example>.rossum.app/api/v1/workflow_steps/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","workflow":"https://<example>.rossum.app/api/v1/workflows/75","condition":{},"type":"approval","mode":"all","ordering":1}
```

{"id":7540,"name":"Team Lead approval step","url":"https://<example>.rossum.app/api/v1/workflow_steps/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","workflow":"https://<example>.rossum.app/api/v1/workflows/75","condition":{},"type":"approval","mode":"all","ordering":1}
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the workflow steptruenamestringName of the workflow stepurlURLURL of the workflow steptrueorganizationURLURL of the organizationworkflowURLURL of the workflowconditionJSONCondition that designates whether the workflow step will be enteredtypestringapprovalType of the workflow step (currently the only supported value isapproval)modestringSupported values:any- approval of one assignee is enough,all- all assignees must approve,auto- automatically approved if the condition matches.orderingintegerDesignates the evaluation order of steps within a workflow (must be unique per a workflow)
approval
approval
any
all
auto

### List all workflow steps

List all workflow steps

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_Steps'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_Steps'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"name":"Team Lead approval step","url":"https://<example>.rossum.app/api/v1/workflow_steps/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","workflow":"https://<example>.rossum.app/api/v1/workflows/75","condition":{},"type":"approval","mode":"all","ordering":1}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"name":"Team Lead approval step","url":"https://<example>.rossum.app/api/v1/workflow_steps/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","workflow":"https://<example>.rossum.app/api/v1/workflows/75","condition":{},"type":"approval","mode":"all","ordering":1}]}
GET /v1/workflow_steps
GET /v1/workflow_steps
Retrieve all workflow step objects.
Supported filters:id,workflow,mode,type
id
workflow
mode
type
Supported ordering:id
id
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofworkflow stepsobjects.

### Retrieve a workflow step

Get workflow step object7694
7694

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_steps/7694'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_steps/7694'

```
{"id":7540,"name":"Team Lead approval step","url":"https://<example>.rossum.app/api/v1/workflow_steps/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","workflow":"https://<example>.rossum.app/api/v1/workflows/75","condition":{},"type":"approval","mode":"all","ordering":1}
```

{"id":7540,"name":"Team Lead approval step","url":"https://<example>.rossum.app/api/v1/workflow_steps/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","workflow":"https://<example>.rossum.app/api/v1/workflows/75","condition":{},"type":"approval","mode":"all","ordering":1}
GET /v1/workflow_steps/{id}
GET /v1/workflow_steps/{id}
Get a workflow step object.

#### Response

Status:200
200
Returnsworkflow stepobject.


## Workspace

Example workspace object

```
{"id":7540,"name":"East West Trading Co","url":"https://<example>.rossum.app/api/v1/workspaces/7540","autopilot":true,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8236"],"metadata":{}}
```

{"id":7540,"name":"East West Trading Co","url":"https://<example>.rossum.app/api/v1/workspaces/7540","autopilot":true,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8236"],"metadata":{}}
A workspace object is a container ofqueueobjects.
AttributeTypeDefaultDescriptionRead-onlyidintegerId of the workspacetruenamestringName of the workspaceurlURLURL of the workspacetrueautopilotbool(Deprecated) Whether to automatically confirm datapoints (hide eyes) from previously seen annotationstrueorganizationURLRelated organizationqueueslist[URL][]List of queues that belongs to the workspacetruemetadataobject{}Client data.
{}

### List all workspaces

List all workspaces

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workspaces'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workspaces'

```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"name":"East West Trading Co","url":"https://<example>.rossum.app/api/v1/workspaces/7540","autopilot":true,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8236"],"metadata":{}}]}
```

{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"name":"East West Trading Co","url":"https://<example>.rossum.app/api/v1/workspaces/7540","autopilot":true,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8236"],"metadata":{}}]}
GET /v1/workspaces
GET /v1/workspaces
Retrieve all workspace objects.
Supported filters:id,name,organization
id
name
organization
Supported ordering:id,name
id
name
For additional info please refer tofilters and ordering.

#### Response

Status:200
200
Returnspaginatedresponse with a list ofworkspaceobjects.

### Create a new workspace

Create new workspace in organization406namedTest Workspace
406

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Workspace", "organization": "https://<example>.rossum.app/api/v1/organizations/406"}'\'https://<example>.rossum.app/api/v1/workspaces'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Workspace", "organization": "https://<example>.rossum.app/api/v1/organizations/406"}'\'https://<example>.rossum.app/api/v1/workspaces'

```
{"id":7694,"name":"Test Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
```

{"id":7694,"name":"Test Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
POST /v1/workspaces
POST /v1/workspaces
Create a new workspace object.

#### Response

Status:201
201
Returns createdworkspaceobject.

### Retrieve a workspace

Get workspace object7694
7694

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workspaces/7694'
```

curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workspaces/7694'

```
{"id":7694,"name":"Test Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
```

{"id":7694,"name":"Test Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
GET /v1/workspaces/{id}
GET /v1/workspaces/{id}
Get an workspace object.

#### Response

Status:200
200
Returnsworkspaceobject.

### Update a workspace

Update workspace object7694
7694

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "My Workspace", "organization": "https://<example>.rossum.app/api/v1/organizations/406"}'\'https://<example>.rossum.app/api/v1/workspaces/7694'
```

curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "My Workspace", "organization": "https://<example>.rossum.app/api/v1/organizations/406"}'\'https://<example>.rossum.app/api/v1/workspaces/7694'

```
{"id":7694,"name":"My Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
```

{"id":7694,"name":"My Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
PUT /v1/workspaces/{id}
PUT /v1/workspaces/{id}
Update workspace object.

#### Response

Status:200
200
Returns updatedworkspaceobject.

### Update part of a workspace

Update name of workspace object7694
7694

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Important Workspace"}'\'https://<example>.rossum.app/api/v1/workspaces/7694'
```

curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Important Workspace"}'\'https://<example>.rossum.app/api/v1/workspaces/7694'

```
{"id":7694,"name":"Important Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
```

{"id":7694,"name":"Important Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
PATCH /v1/workspaces/{id}
PATCH /v1/workspaces/{id}
Update part of workspace object.

#### Response

Status:200
200
Returns updatedworkspaceobject.

### Delete a workspace

Delete workspace7694
7694

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workspaces/7694'
```

curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workspaces/7694'
DELETE /v1/workspaces/{id}
DELETE /v1/workspaces/{id}
Delete workspace object.

#### Response

Status:204in case of success.409in case the workspace contains queues
204
409


# FAQ


## POST fails with HTTP status 500

Please check that Content-Type header in the HTTP request is set correctly
(e.g.application/json).
application/json
We will improve content type checking in the future , so that  to
return 400.


## SSL connection errors

Rossum API only supports TLS 1.2 to ensure thatup-to-date algorithms and ciphersare used.
Older SSL libraries may not work properly with TLS 1.2. If you encounter
SSL/TLS compatibility issue, please make sure the library supports TLS 1.2 and
the support is switched on.