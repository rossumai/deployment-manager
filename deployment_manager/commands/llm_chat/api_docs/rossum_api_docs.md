
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

> Test curl is installed properly
Test curl is installed properly

```
curl https://<example>.rossum.app/api/v1
```


```
{"organizations":"https://<example>.rossum.app/api/v1/organizations","workspaces":"https://<example>.rossum.app/api/v1/workspaces","schemas":"https://<example>.rossum.app/api/v1/schemas","connectors":"https://<example>.rossum.app/api/v1/connectors","inboxes":"https://<example>.rossum.app/api/v1/inboxes","queues":"https://<example>.rossum.app/api/v1/queues","documents":"https://<example>.rossum.app/api/v1/documents","users":"https://<example>.rossum.app/api/v1/users","groups":"https://<example>.rossum.app/api/v1/groups","annotations":"https://<example>.rossum.app/api/v1/annotations","pages":"https://<example>.rossum.app/api/v1/pages"}
```

All code samples included in this API documentation usecurl, the command
line data transfer tool. On MS Windows 10, MacOS X and most Linux
distributions, curl should already be pre-installed. If not, please download
it fromcurl.haxx.se).
> Optionally usejqtool to pretty-print JSON output
Optionally usejqtool to pretty-print JSON output

```
curl https://<example>.rossum.app/api/v1 | jq
```


```
{"organizations":"https://<example>.rossum.app/api/v1/organizations","workspaces":"https://<example>.rossum.app/api/v1/workspaces","schemas":"https://<example>.rossum.app/api/v1/schemas","connectors":"https://<example>.rossum.app/api/v1/connectors","inboxes":"https://<example>.rossum.app/api/v1/inboxes","queues":"https://<example>.rossum.app/api/v1/queues","documents":"https://<example>.rossum.app/api/v1/documents","users":"https://<example>.rossum.app/api/v1/users","groups":"https://<example>.rossum.app/api/v1/groups","annotations":"https://<example>.rossum.app/api/v1/annotations","pages":"https://<example>.rossum.app/api/v1/pages"}
```

You may also want to installjqtool to make curl output human-readable.

#### Use the API on Windows

This API documentation is written for usage in command line interpreters running on UNIX based operation systems (Linux and Mac).
Windows users may need to use the following substitutions when working with API:

Character used in this documentation | Meaning/usage | Substitute character for Windows users
--- | --- | ---
' | single quotes | "
" | double quotes | "" or \"
\ | continue the command on the next line | ^

> Example of API call on UNIX-based OS
Example of API call on UNIX-based OS

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"target_queue": "https://<example>.rossum.app/api/v1/queues/8236", "target_status": "to_review"}'\'https://<example>.rossum.app/api/v1/annotations/315777/copy'
```

> Examples of API call on Windows
Examples of API call on Windows

```
curl-H"Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03"-H"Content-Type: application/json"^-d"{""target_queue"": ""https://<example>.rossum.app/api/v1/queues/8236"", ""target_status"": ""to_review""}"^"https://<example>.rossum.app/api/v1/annotations/315777/copy"curl-H"Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03"-H"Content-Type: application/json"^-d"{\"target_queue\":\"https://<example>.rossum.app/api/v1/queues/8236\",\"target_status\":\"to_review\"}"^"https://<example>.rossum.app/api/v1/annotations/315777/copy"
```


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

```
curl -s -H 'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03' \
  'https://<example>.rossum.app/api/v1/annotations/319668' | jq .status
"to_review"
```

After that, you can open the Rossum web interfaceexample.rossum.appto review and confirm extracted data.

#### Download reviewed data

Now you can export extracted data using theexportendpoint of the queue. You
can select XML, CSV, XLSX or JSON format. For CSV, use URL like:

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

## Base URL

Base API endpoint URL depends on the account type, deployment and location. Default URL ishttps://<example>.rossum.app/apiwhere theexampleis the domain selected during the account creation.
URLs of companies using a dedicated deployment may look likehttps://acme.rossum.app/api.
If you are not sure about the correct URL you can navigate tohttps://app.rossum.aiand use your email address
to receive your account information via email.
Please note that we previously recommended using thehttps://api.elis.rossum.aiendpoint to interact with the Rossum
API, but now it is deprecated. For new integrations use the newhttps://<example>.rossum.app/apiendpoint.
For accounts created before Nov 2022 use thehttps://elis.rossum.ai/api.

## Authentication

Most of the API endpoints require a user to be authenticated. To login to the Rossum
API, post an object withusernameandpasswordfields. Login returns an access key
to be used for token authentication.
Our API also provide possibility to authenticate via One-Time token which is returned after registration.
This tokens allows users to authenticate against our API, but after one call, this token will be invalidated.
This token can be exchanged for regular access token limited only by the time of validity. For the
purpose of token exchange, use the/auth/tokenendpoint.
Users may delete a token using the logout endpoint or automatically after a
configured time (the default expiration time is 162 hours). The default expiration time can be lowered usingmax_token_lifetime_sfield. When the token expires, 401 status is returned.
Users are expected to re-login to obtain a new token.
Rossum's API also supports session authentication, where a user session is created inside cookies after login.
If enabled, the session lasts 1 day until expired by itself or until logout
While the session is valid there is no need to send the authentication token in every request, but the "unsafe" request (POST, PUT, PATCH, DELETE),
whose MIME type is different fromapplication/jsonmust includeX-CSRFTokenheader with valid CSRF token, which is returned inside Cookie while loging in.
When a session expires, 401 status is returned as with token authentication, and users are expected to re-login to start a new session.

### Login

> Login user using username and password
Login user using username and password

```
curl-H'Content-Type: application/json'\-d'{"username": "east-west-trading-co@<example>.rossum.app", "password": "aCo2ohghBo8Oghai"}'\'https://<example>.rossum.app/api/v1/auth/login'
```


```
{"key":"db313f24f5738c8e04635e036ec8a45cdd6d6b03","domain":"acme-corp.app.rossum.ai"}
```

> Use token key in requests
Use token key in requests

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/406'
```

> Note: The Token authorization scheme is also supported for compatibility with earlier versions.
Note: The Token authorization scheme is also supported for compatibility with earlier versions.

```
curl-H'Authorization: Token db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/406'
```

> Login user expiring after 1 hour
Login user expiring after 1 hour

```
curl-H'Content-Type: application/json'\-d'{"username": "east-west-trading-co@<example>.rossum.app", "password": "aCo2ohghBo8Oghai", "max_token_lifetime_s": 3600}'\'https://<example>.rossum.app/api/v1/auth/login'
```


```
{"key":"ltcg2p2w7o9vxju313f04rq7lcc4xu2bwso423b3","domain":null}
```


Attribute | Type | Required | Description
--- | --- | --- | ---
username | string | true | Username of the user to be logged in.
password | string | true | Password of the user.
origin | string | false | For internal use only. Using this field may affectthrottlingof your API requests.
max_token_lifetime_s | integer | false | Duration (in seconds) for which the token will be valid. Default is 162 hours which is also the maximum.


#### Response

Returns object with "key", which is an access token. And the user's domain.

Attribute | Type | Description
--- | --- | ---
key | string | Access token.
domain | string | The domain the token was issued for.


### Logout

> Logout user

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/auth/logout'
```


```
{"detail":"Successfully logged out."}
```

Logout user, discard auth token.

#### Response


### Token Exchange

> Exchange One-Time authentication token with a longer-lived access token.
Exchange One-Time authentication token with a longer-lived access token.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/auth/token'
```


```
{"key":"ltcg2p2w7o9vxju313f04rq7lcc4xu2bwso423b3","domain":"<example>.rossum.app","scope":"default"}
```


Attribute | Type | Required | Description
--- | --- | --- | ---
scope | string | false | Supported values aredefault,approval(for internal use only)
max_token_lifetime_s | float | false | Duration (in seconds) for which the token will be valid (default: lifetime of the current token or 162 hours if the current token is one-time). Can be set to a maximum of 583200 seconds (162 hours).
origin | string | false | For internal use only. Using this field may affectthrottlingof your API requests.

This endpoint enables the exchange of a one-time token for a longer lived access token.
It is able to receive either one-time tokens provided after registration, or JWT tokens if you have such a setupconfigured. The token must be provided in a theBearerauthorization header.

### JWT authentication

Short-lived JWT tokens can be exchanged for access tokens. A typical use case, for example, is logging in your users via SSO in your own application, and displaying the Rossum app to them embedded.
To enable JWT authentication, one needs to provide Rossum with the public key that shall be used to decode the tokens.
Currently only tokens with EdDSA (signed usingEd25519andEd448curves) and RS512 signatures are allowed, and token validity should be 60 seconds maximum.
The expected formats of the header and encoded payload of the JWT token are as follows:

### Decoded JWT Header Format

> Example format of a decoded JWT token header (not encrypted)
Example format of a decoded JWT token header (not encrypted)

```
{"alg":"EdDSA","kid":"urn:rossum.ai:organizations:100","typ":"JWT"}
```

> Example format of a decoded JWT token payload
Example format of a decoded JWT token payload

```
{"ver":"1.0","iss":"ACME Corporation","aud":"https://<example>.rossum.app","sub":"john.doe@rossum.ai","exp":1514764800,"email":"john.doe@rossum.ai","name":"John F. Doe","rossum_org":"100","roles":["annotator"]}
```


Attribute | Type | Required | Description
--- | --- | --- | ---
kid | string | true | Identifier. Must end with:{your Rossum org ID}, e.g."urn:rossum.ai:organizations:123"
typ | string | false | Type of the token.
alg | string | true | Signature algorithm to be used for decoding the token. OnlyEdDSAorRS512values are allowed.


### Decoded JWT Payload Format


Attribute | Type | Required | Description
--- | --- | --- | ---
ver | string | true | Version of the payload format. Available versions:1.0.
iss | string | true | Name of the issuer of the token (e.g. company name).
aud | string | true | Target domain used for API queries (e.g.https://<example>.rossum.app)
sub | string | true | User email that will be matched against username in Rossum.
exp | int | true | UNIX timestamp of the JWT token expiration. Must be set to 60 seconds after current UTC time at maximum.
email | string | true | User email.
name | string | true | User's first name and last name separated by space. Will be used for creation of new users if auto-provisioning is enabled.
rossum_org | string | true | Rossum organization id.
roles | list[string] | false | Name of theuser rolesthat will be assigned to user created by auto-provisioning. Must be a subset of the roles stated in the auto-provisioning configuration for the organization.


#### Response


Attribute | Type | Description
--- | --- | ---
key | string | Access token.
domain | string | The domain the token was issued for.
scope | string | Supported values aredefault,approval(for internal use only)


### Single Sign-On (SSO)

Rossum allows customers to integrate with their ownidentity provider,
such asGoogle,Azure ADor any other provider usingOAuth2 OpenID Connectprotocol (OIDC).
Rossum then acts as aservice provider.
When SSO is enabled for an organization, user is redirected to a configured identity provider login page
and only allowed to access Rossum application when successfully authenticated.
Identity provider user claim (e.g.email(default),sub,preferred_username,unique_name)
is used to match a user account in Rossum. If auto-provisioning is enabled for
the organization, user accounts in Rossum will be automatically created for users without accounts.
Required setup of the OIDC identity provider:
- Redirect URI (also known as Reply URL):https://<example>.rossum.app/api/v1/oauth/code
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

Parameter | Default | Maximum | Description
--- | --- | --- | ---
page_size | 20 | 100(*) | Number of results per page
page | 1 |  | Page of results

(*)Maximum page size differs for some endpoints:
- 1,000 for exporting data in CSV format via POST on /annotations
- 500 for searching in annotations via annotations/search (ifsideload=contentis not included)

## API Throttling

To ensure optimal performance and fair usage across the platform, the API implements throttling features. If a client exceeds the allowed
number of API requests Rossum API will respond with a429status code and aRetry-Afterheader.
The header specifies the number of seconds the client should wait before retrying the request.
To avoid being throttled, ensure your usage complies with our Acceptable Use Schedule as described in theRossum Terms of Use.
When the client receives a429status code, the response headerRetry-Afterwill have the following format:
This example means the client should wait for 10 seconds before attempting another request.
The recommended approach for handling throttled requests is to manage429status codes gracefully and use
exponential backoff for retries, respecting theRetry-Afterheader.

### Current Throttling Limits

The current default throttling limits for Rossum API are as follows:

Limit | Description
--- | ---
10 reqs / second | Overall API rate limit.
10 reqs / minute | Limit specific for theannotations/{id}/page_data/translateendpoint.


## Filters and ordering

> List queues of workspace7540, with localeen_USand order results byname.
List queues of workspace7540, with localeen_USand order results byname.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues?workspace=7540&locale=en_US&ordering=name'
```

Lists may be filtered using various attributes.
Multiple attributes are combined with&in the URL, which results in more specific response.
Please refer to the particularobject description.
Ordering of results may be enforced by theorderingparameter and one or more
keys delimited by a comma. Preceding key with a minus sign-enforces
descending order.

## Metadata

> Example metadata in a document object
Example metadata in a document object

```
{"id":319768,"url":"https://<example>.rossum.app/api/v1/documents/319768","s3_name":"05feca6b90d13e389c31c8fdeb7fea26","annotations":["https://<example>.rossum.app/api/v1/annotations/319668"],"mime_type":"application/pdf","arrived_at":"2019-02-11T19:22:33.993427Z","original_file_name":"document.pdf","content":"https://<example>.rossum.app/api/v1/documents/319768/content","metadata":{"customer-id":"f205ec8a-5597-4dbb-8d66-5a53ea96cdea","source":9581,"authors":["Joe Smith","Peter Doe"]}}
```

When working with API objects, it may be useful to attach some information to
the object (e.g. customer id to a document). You can store custom JSON object
in ametadatasection available in most objects.
List of objects with metadata support: organization, workspace, user, queue, schema,
connector, inbox, document, annotation, page, survey.
Total metadata size may be up to 4 kB per object.

## Versioning

API Version is part of the URL, e.g.https://<example>.rossum.app/api/v1/users.
To allow API progress, we consideradditionof a field in a JSON object as well asadditionof a new item in an enum object to be backward-compatible operations that
may be introduced at any time. Clients are expected to deal with such changes.

## Dates

All dates fields are represented asISO 8601formatted strings, e.g.2018-06-01T21:36:42.223415Z. All returned dates are in UTC timezone.

## Errors

Our API uses conventional HTTP response codes to indicate the success or failure of an API request.

Code | Status | Meaning
--- | --- | ---
400 | Bad Request | Invalid input data or error from connector.
401 | Unauthorized | The username/password is invalid or token is invalid (e.g. expired).
403 | Forbidden | Insufficient permission, missing authentication, invalid CSRF token and similar issues.
404 | Not Found | Entity not found (e.g. already deleted).
405 | Method Not Allowed | You tried to access an endpoint with an invalid method.
409 | Conflict | Trying to change annotation that was not started by the current user.
413 | Payload Too Large | for too large payload (especially for files uploaded).
429 | Too Many Requests | The allowed number of requests per minute has been exceeded. Please wait before sending more requests.
500 | Internal Server Error | We had a problem with the server. Try again later.
503 | Service Unavailable | We're temporarily offline for maintenance. Please try again later.


# Import and Export

Documents may be imported into Rossum using the REST API and email gateway.
Supported file formats arePDF,PNG,JPEG,TIFF,XLSX/XLSandDOCX/DOC.
Maximum supported file size is 40 MB (this limit applies also to the uncompressed size of the files within a.ziparchive).
In order to get the best results from Rossum the documents should be in A4
format of at least 150 DPI (in case of scans/photos). Read more aboutimport recommendations.

## Importing non-standard MIME types

Support for additional MIME types may be added by handlingupload.createdwebhook event. With this setup, user is able to pre-process
uploaded files (e.g.XMLorJSONformats) into a format that Rossum understands. Those usually need to be enabled on queue level first
(by adding appropriate mimetype toaccepted_mime_typesin queue settings attributes).
List of enabled MIME types:
- application/EDI-X12
- application/EDIFACT
- application/json
- application/msword
- application/pdf
- application/pgp-encrypted
- application/vnd.ms-excel
- application/vnd.ms-outlook
- application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- application/vnd.openxmlformats-officedocument.wordprocessingml.document
- application/xml
- application/zip
- image/*
- message/rfc822
- text/csv
- text/plain
- text/xml
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
Invalid characters in attachment file names (e.g./) are replaced with underscores.
Small images (up to 100x100 pixels) are ignored, seeinboxfor reference.
You can use selected email header data (e.g. Subject) to initialize additional
field values, seerir_field_namesattributedescriptionfor details.
Zip attachment limits:
- the uncompressed size of the files within a.ziparchive may not exceed 40 MB
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

# Document Schema

Every queue has an associated schema that specifies which fields will be
extracted from documents as well as the structure of the data sent to
connector and exported from the platform.
Rossum schema supports data fields with single values (datapoint),
fields with multiple values (multivalue) or tuples of fields (tuple). At the
topmost level, each schema consists ofsections, which may either directly
contain actual data fields (datapoints) or use nestedmultivalues andtuples as
containers for single datapoints.
But while schema may theoretically consist of an arbitrary number of nested containers,
the Rossum UI supports only certain particular combinations of datapoint types.
The supported shapes are:simple:atomic datapoints of typenumber,string,dateorenumlist:simple datapoint within a multivaluetabular:simple datapoint within a "multivalue tuple" (a multivalue list containing a tuple for every row)
- simple:atomic datapoints of typenumber,string,dateorenum
- list:simple datapoint within a multivaluetabular:simple datapoint within a "multivalue tuple" (a multivalue list containing a tuple for every row)

## Schema content

Schema content consists of a list ofsectionobjects.

### Common attributes

The following attributes are common for all schema objects:

Attribute | Type | Description | Required
--- | --- | --- | ---
category | string | Category of an object, one ofsection,multivalue,tupleordatapoint. | yes
id | string | Unique identifier of an object. Maximum length is 50 characters. | yes
label | string | User-friendly label for an object, shown in the user interface | yes
hidden | boolean | If set totrue, the object is not visible in the user interface, but remains stored in the database and may be exported. Default is false. Note thatsectionis hidden if all its children are hidden. | no
disable_prediction | boolean | Can be set totrueto disable field extraction, while still preserving the data shape. Ignored by aurora engines. | no


### Section

> Example of a section

```
{"category":"section","id":"amounts_section","label":"Amounts","children":[...],"icon":""}
```

Section represents a logical part of the document, such as amounts or vendor info.
It is allowed only at the top level. Schema allows multiple sections, and there should
be at least one section in the schema.

Attribute | Type | Description | Required
--- | --- | --- | ---
children | list[object] | Specifies objects grouped under a given section. It can containmultivalueordatapointobjects. | yes
icon | string | The icon that appears on the left panel in the UI for a given section (not yet supported on UI). | 


### Datapoint

A datapoint represents a single value, typically a field of a document or some global document information.
Fields common to all datapoint types:

Attribute | Type | Description | Required
--- | --- | --- | ---
type | string | Data type of the object, must be one of the following:string,number,date,enum,button | yes
can_export | boolean | If set tofalse, datapoint is not exported throughexport endpoint. Default is true. | 
can_collapse | boolean | If set totrue, tabular (multivalue-tuple) datapoint may be collapsed in the UI. Default is false. | 
rir_field_names | list[string] | List of references used to initialize an object value. Seebelowfor the description. | 
default_value | string | Default value used either for fields that do not use hints from AI engine predictions (i.e.rir_field_namesare not specified), or when the AI engine does not return any data for the field. | 
constraints | object | A map of various constraints for the field. SeeValue constraints. | 
ui_configuration | object | A group of settings affecting behaviour of the field in the application. SeeUI configuration. | 
width | integer | Width of the column (in characters). Default widths are: number: 8, string: 20, date: 10, enum: 20. Only supported for table datapoints. | 
stretch | boolean | If total width of columns doesn’t fill up the screen, datapoints with stretch set to true will be expanded proportionally to other stretching columns. Only supported for table datapoints. | 
width_chars | integer | (Deprecated) Usewidthandstretchproperties instead. | 
score_threshold | float [0;1] | Threshold used to automatically validate field content based onAI confidence scores. If not set,queue.default_score_thresholdis used. | 
formula | string[0;2000] | Formula definition, required only for fields of typeformula, seeFormula Fields.rir_field_namesshould also be empty for these fields. | 
prompt | string[0;2000] | Prompt definition, required only for fields of typereasoning. | 
context | list[string] | Context for the prompt, required only for fields of typereasoningseeLogical Types. | 

rir_field_namesattribute allows to specify source of initial value of the object. List items may be:
- one ofextracted field typesto use the AI engine prediction value
- upload:idto identify a value specified whileuploadingthe document
- edit:idto identify a value specified inedit_pagesendpoint
- email_header:<id>to use a value extracted from email headers. Supported email headers:from,to,reply-to,subject,message-id,date.
- email_body:<id>to select email body. Supported values aretext_htmlfor HTML body ortext_plainfor plain text body.
- email:<id>to identify a value specified inemail.receivedhook response
- emails_import:<id>to identify a value specified in thevaluesparameter whenimporting an email.
If more list items inrir_field_namesare specified, the first available value will be used.

#### String type

> Example string datapoint
Example string datapoint

```
{"category":"datapoint","id":"document_id","label":"Invoice ID","type":"string","default_value":null,"rir_field_names":["document_id"],"constraints":{"length":{"exact":null,"max":16,"min":null},"regexp":{"pattern":"^INV[0-9]+$"},"required":false}}
```

String datapoint does not have any special attribute.

#### Date type

> Example date datapoint
Example date datapoint

```
{"id":"item_delivered","type":"date","label":"Item Delivered","format":"MM/DD/YYYY","category":"datapoint"}
```

Attributes specific to Date datapoint:

Attribute | Type | Description | Required
--- | --- | --- | ---
format | string | Enforces a format fordatedatapoint on the UI. SeeDate formatbelow for more details. Default isYYYY-MM-DD. | 

Date format supported:available tokens
Example date formats:
- D/M/YYYY: e.g. 23/1/2019
- MM/DD/YYYY: e.g. 01/23/2019
- YYYY-MM-DD: e.g. 2019-01-23 (ISO date format)

#### Number type

> Example number datapoint
Example number datapoint

```
{"id":"item_quantity","type":"number","label":"Quantity","format":"#,##0.#","category":"datapoint"}
```

Attributes specific to Number datapoint:

Attribute | Type | Default | Description | Required
--- | --- | --- | --- | ---
format | string | # ##0.# | Available choices for number format show table below.nullvalue is allowed. | 
aggregations | object |  | A map of various aggregations for the field. Seeaggregations. | 

The following table shows numeric formats with their examples.

Format | Example
--- | ---
# ##0,# | 1 234,5 or 1234,5
# ##0.# | 1 234.5 or 1234.5
#,##0.# | 1,234.5 or 1234.5
#'##0.# | 1'234.5 or 1234.5
#.##0,# | 1.234,5 or 1234,5
# ##0 | 1 234 or 1234
#,##0 | 1,234 or 1234
#'##0 | 1'234 or 1234
#.##0 | 1.234 or 1234

> Example aggregations

```
{"id":"quantity","type":"number","label":"Quantity","category":"datapoint","aggregations":{"sum":{"label":"Total"}},"default_value":null,"rir_field_names":[]}
```

Aggregations allow computation of some informative values, e.g. a sum of a table column with numeric values.
These are returned amongmessageswhen/v1/annotations/{id}/content/validateendpointis called.
Aggregations can be computed only for tables (multivaluesoftuples).

Attribute | Type | Description | Required
--- | --- | --- | ---
sum | object | Sum of values in a column. Defaultlabel: "Sum". | 

All aggregation objects can have an attributelabelthat will be shown in the UI.

#### Enum type

> Example enum datapoint with options and enum_value_type
Example enum datapoint with options and enum_value_type

```
{"id":"document_type","type":"enum","label":"Document type","hidden":false,"category":"datapoint","options":[{"label":"Invoice Received","value":"21"},{"label":"Invoice Sent","value":"22"},{"label":"Receipt","value":"23"}],"default_value":"21","rir_field_names":[],"enum_value_type":"number"}
```

Attributes specific to Enum datapoint:

Attribute | Type | Description | Required
--- | --- | --- | ---
options | object | See object description below. | yes
enum_value_type | string | Data type of the option's value attribute. Must be one of the following:string,number,date | no

Every option consists of an object with keys:

Attribute | Type | Description | Required
--- | --- | --- | ---
value | string | Value of the option. | yes
label | string | User-friendly label for the option, shown in the UI. | yes

Enum datapoint value is matched in a case insensitive mode, e.g.EURcurrency value returned by the AI Core Engine is
matched successfully against{"value": "eur", "label": "Euro"}option.

#### Button type

Specifies a button shown in Rossum UI. For more details please refer tocustom UI extension.
> Example button datapoint
Example button datapoint

```
{"id":"show_email","type":"button","category":"datapoint","popup_url":"http://example.com/show_customer_data","can_obtain_token":true}
```

Buttons cannot be direct children of multivalues (simple multivalues with buttons are not allowed. In tables, buttons are children of tuples).
Despite being a datapoint object, button currently cannot hold any value. Therefore, the set of available Button datapoint attributes is limited to:

Attribute | Type | Description | Required
--- | --- | --- | ---
type | string | Data type of the object, must be one of the following:string,number,date,enum,button | yes
can_export | boolean | If set tofalse, datapoint is not exported throughexport endpoint. Default is true. | 
can_collapse | boolean | If set totrue, tabular (multivalue-tuple) datapoint may be collapsed in the UI. Default is false. | 
popup_url | string | URL of a popup window to be opened when button is pressed. | 
can_obtain_token | boolean | If set totruethe popup window is allowed to ask the main Rossum window for authorization token | 


#### Value constraints

> Example value constraints
Example value constraints

```
{"id":"document_id","type":"string","label":"Invoice ID","category":"datapoint","constraints":{"length":{"max":32,"min":5},"required":false},"default_value":null,"rir_field_names":["document_id"]}
```

Constraints limit allowed values. When constraints is not satisfied, annotation is considered invalid and cannot be exported.

Attribute | Type | Description | Required
--- | --- | --- | ---
length | object | Defines minimum, maximum or exact length for the datapoint value. By default, minimum and maximum are0and infinity, respectively. Supported attributes:min,maxandexact | 
regexp | object | When specified, content must match a regular expression. Supported attributes:pattern. To ensure that entire value matches, surround your regular expression with^and$. | 
required | boolean | Specifies if the datapoint is required by the schema. Default value istrue. | 


#### UI configuration

> Example UI configuration
Example UI configuration

```
{"id":"document_id","type":"string","label":"Invoice ID","category":"datapoint","ui_configuration":{"type":"captured","edit":"disabled"},"default_value":null,"rir_field_names":["document_id"]}
```

UI configuration provides a group of settings, which alter behaviour of the field in the application. This does not affect behaviour of the field via the API.
For example, disablingeditprohibits changing a value of the datapoint in the application, but the value can still be modified through API.

Attribute | Type | Description | Required
--- | --- | --- | ---
type | string | Logical type of the datapoint. Possible values are:captured,data,manual,formula,reasoningornull. Default value isnull. | false
edit | string | When set todisabled, value of the datapoint is not editable via UI. When set toenabled_without_warning, no warnings are displayed in the UI regarding this fields editing behaviour. Default value isenabled, this option enables field editing, but user receives dismissible warnings when doing so. | false

- Captured fieldrepresents information retrieved by the OCR model. If combined witheditoption disabled, user can't overwrite field's value, but is able to redraw field's bounding box and select another value from the document by such an action.
- Data fieldrepresents information filled by extensions. This field is not mapped to the AI model, so it does not have a bounding box, neither it's possible to create one. If combined witheditoption disabled the field can't be modified from the UI.
- Manual fieldbehaves exactly likeData field, without the mapping to extensions. This field should be used for sharing information between users or to transfer information to downstream systems.
- Formula fieldThis field will be updated according to itsformuladefinition, seeFormula Fields. If theeditoption is not disabled the field value can be overridden from the UI (seeno_recalculation).
- Reasoning fieldsThis field will be updated according to itspromptandcontext.contextsupports adding related schema fields in a format of TxScript strings (e.g.field.invoice_id, alsoself.attr.labelandself.attr.descriptionare supported). If theeditoption is not disabled the field value can be overridden from the UI (seeno_recalculation).
- nullvalue is displayed in UI asUnsetand behaves similar to theCaptured field.

### Multivalue

> Example of a multivalue:
Example of a multivalue:

```
{"category":"multivalue","id":"line_item","label":"Line Item","children":{...},"show_grid_by_default":false,"min_occurrences":null,"max_occurrences":null,"rir_field_names":null}
```

> Example of a multivalue with grid row-types specification:
Example of a multivalue with grid row-types specification:

```
{"category":"multivalue","id":"line_item","label":"Line Item","children":{...},"grid":{"row_types":["header","data","footer"],"default_row_type":"data","row_types_to_extract":["data"]},"min_occurrences":null,"max_occurrences":null,"rir_field_names":["line_items"]}
```

Multivalue is list ofdatapoints ortuples of the same type.
It represents a container for data with multiple occurrences
(such as line items) and can contain only objects with the sameid.

Attribute | Type | Description | Required
--- | --- | --- | ---
children | object | Object specifying type of children. It can contain only objects with categoriestupleordatapoint. | yes
min_occurrences | integer | Minimum number of occurrences of nested objects. If condition of min_occurrences is violated corresponding fields should be manually reviewed. Minimum required value for the field is 0. If not specified, it is set to 0 by default. | 
max_occurrences | integer | Maximum number of occurrences of nested objects. All additional rows above max_occurrences are removed by extraction process. Minimum required value for the field is 1. If not specified, it is set to 1000 by default. | 
grid | object | Configure magic-grid feature properties, seebelow. | 
show_grid_by_default | boolean | If set totrue, the magic-grid is opened instead of footer upon entering the multivalue. Defaultfalse. Applied only in UI. Useful when annotating documents for custom training. | 
rir_field_names | list[string] | List of names used to initialize content from the AI engine predictions. If specified, the value of the first field from the array is used, otherwise default nameline_itemsis used. Attribute can be set only for multivalue containing objects with categorytuple. | no


#### Multivalue grid object

Multivaluegridobject allows to specify arow typefor each row of the
grid. For data representation of actual grid data rows seeGrid object description.

Attribute | Type | Description | Default | Required
--- | --- | --- | --- | ---
row_types | list[string] | List of allowed row type values. | ["data"] | yes
default_row_type | string | Row type to be used by default | data | yes
row_types_to_extract | list[string] | Types of rows to be extracted to related table | ["data"] | yes

For example to distinguish two header types and a footer in the validation interface, following row types may be used:header,subsection_header,dataandfooter.
Currently, data extraction classifies every row as eitherdataorheader(additional row types may be introduced
in the future). We remove rows returned by data extraction that are not inrow_typeslist (e.g.headerby
default) and are on the top/bottom of the table. When they are in the middle of the table, we mark them as skipped
(null).
There are three visual modes, based onrow_typesquantity:
- More than two row types defined: User selects row types freely to any non-default row type. Clearing row type resets to a default row type. We support up to 6 colors to easily distinguish row types visually.
- Two row types defined (header and default): User only marks header and skipped rows. Clearing row type resets to a default row type.
- One row type defined: User is only able to mark row as skipped (nullvalue in data). This is also a default behavior when nogridrow types configuration is specified in the schema.

### Tuple

> Example of a tuple:

```
{"category":"tuple","id":"tax_details","label":"Tax Details","children":[...],"rir_field_names":["tax_details"]}
```

Container representing tabular data with related values, such as tax details.
Atuplemust be nested within amultivalueobject, but unlikemultivalue,
it may consist of objects with differentids.

Attribute | Type | Description | Required
--- | --- | --- | ---
children | list[object] | Array specifying objects that belong to a giventuple. It can contain only objects with categorydatapoint. | yes
rir_field_names | list[string] | List of names used to initialize content from the AI engine predictions. If specified, the value of the first extracted field from the array is used, otherwise, no AI engine initialization is done for the object. | 


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
- Recommendation: Edit existing schema (see Use case 1). Data of already created annotations will be transformed to the shape of the updated schema. New fields of annotations into_reviewandpostponedstate that are linked toextracted fields typeswill be filled byAI Engine, if available. New fields for alreadyexportedordeletedannotations (alsopurged,exportingandfailed_export) will be filled with empty or default values.
Use case 4 - Adding new field to schema, only for newly imported documents
- Situation: User is extending a production schema by adding a new field. However, with the intention that the user does not want to see the newly added field on previously created annotations.
- Recommendation:Create a new schema object(POST) and link it to the queue. Annotation data of previously created annotations will be preserved according to the original schema. This approach is recommended if there is an organizational need to keep different field sets before and after the schema update.
Use case 5 - Deleting schema field, even for already imported documents.
- Situation: User is changing a production schema by removing a field that was used previously. However, user would like to see all annotations (to_review,postponed,exported,deleted, etc. states) in the look of the newly extended schema. There is no need to see the original fields in already exported annotations.
- Recommendation: Edit existing schema (see Use case 1).
Use case 6 - Deleting schema field, only for newly imported documents
- Situation: User is changing a production schema by removing a field that was used previously. However, with the intention that the user will still be able to see the removed fields on previously created annotations.
- Recommendation: Create a new schema object (see Use case 4). Annotation data of previously created annotations will be preserved according to the original schema. This approach is recommended if there is an organizational need to retrieve the data in the original state.

### Preserving data on schema change

In order to transfer annotation fieldvaluesproperly during the schema update,
a datapoint'scategoryandschema_idmust be preserved.
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

### Identifiers

> Example of a schema with different identifiers:
Example of a schema with different identifiers:

```
[{"category":"section","children":[{"category":"datapoint","constraints":{"required":false},"default_value":null,"id":"document_id","label":"Invoice number","rir_field_names":["document_id"],"type":"string"},{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"D/M/YYYY","id":"date_issue","label":"Issue date","rir_field_names":["date_issue"],"type":"date"},{"category":"datapoint","constraints":{"required":false},"default_value":null,"id":"terms","label":"Terms","rir_field_names":["terms"],"type":"string"}],"icon":null,"id":"invoice_info_section","label":"Basic information"}]
```


Attr. rir_field_names | Field label | Description
--- | --- | ---
account_num | Bank Account | Bank account number. Whitespaces are stripped.
bank_num | Sort Code | Sort code. Numerical code of the bank.
iban | IBAN | Bank account number in IBAN format.
bic | BIC/SWIFT | Bank BIC or SWIFT code.
const_sym | Constant Symbol | Statistical code on payment order.
spec_sym | Specific Symbol | Payee id on the payment order, or similar.
var_sym | Variable symbol | In some countries used by the supplier to match the payment received against the invoice. Possible non-numeric characters are stripped.
terms | Terms | Payment terms as written on the document (e.g. "45 days", "upon receipt").
payment_method | Payment method | Payment method defined on a document (e.g. 'Cheque', 'Pay order', 'Before delivery')
customer_id | Customer Number | The number by which the customer is registered in the system of the supplier. Whitespaces are stripped.
date_due | Date Due | The due date of the invoice.
date_issue | Issue Date | Date of issue of the document.
date_uzp | Tax Point Date | The date of taxable event.
document_id | Document Identifier | Document number. Whitespaces are stripped.
order_id | Order Number | Purchase order identification (Order Numbers not captured as "sender_order_id"). Whitespaces are stripped.
recipient_address | Recipient Address | Address of the customer.
recipient_dic | Recipient Tax Number | Tax identification number of the customer. Whitespaces are stripped.
recipient_ic | Recipient Company ID | Company identification number of the customer. Possible non-numeric characters are stripped.
recipient_name | Recipient Name | Name of the customer.
recipient_vat_id | Recipient VAT Number | Customer VAT Number
recipient_delivery_name | Recipient Delivery Name | Name of the recipient to whom the goods will be delivered.
recipient_delivery_address | Recipient Delivery Address | Address of the reciepient where the goods will be delivered.
sender_address | Supplier Address | Address of the supplier.
sender_dic | Supplier Tax Number | Tax identification number of the supplier. Whitespaces are stripped.
sender_ic | Supplier Company ID | Business/organization identification number of the supplier. Possible non-numeric characters are stripped.
sender_name | Supplier Name | Name of the supplier.
sender_vat_id | Supplier VAT Number | VAT identification number of the supplier.
sender_email | Supplier Email | Email of the sender.
sender_order_id | Supplier's Order ID | Internal order ID in the suppliers system.
delivery_note_id | Delivery Note ID | Delivery note ID defined on the invoice.
supply_place | Place of Supply | Place of supply (the name of the city or state where the goods will be supplied).


### Document attributes


Attr. rir_field_names | Field label | Description
--- | --- | ---
currency | Currency | The currency which the invoice is to be paid in. Possible values: AED, ARS, AUD, BGN, BRL, CAD, CHF, CLP, CNY, COP, CRC, CZK, DKK, EUR, GBP, GTQ, HKD, HUF, IDR, ILS, INR, ISK, JMD, JPY, KRW, MXN, MYR, NOK, NZD, PEN, PHP, PLN, RON, RSD, SAR, SEK, SGD, THB, TRY, TWD, UAH, USD, VES, VND, ZAR or other. May be also in lowercase.
document_type | Document Type | Possible values: credit_note, debit_note, tax_invoice (most typical), proforma, receipt, delivery_note, order or other.
language | Language | The language which the document was written in. Values are ISO 639-3 language codes, e.g.: eng, fra, deu, zho. SeeLanugages Supported By Rossum
payment_method_type | Payment Method Type | Payment method used for the transaction. Possible values: card, cash.


### Amounts


Attr. rir_field_names | Field label | Description
--- | --- | ---
amount_due | Amount Due | Final amount including tax to be paid after deducting all discounts and advances.
amount_rounding | Amount Rounding | Remainder after rounding amount_total.
amount_total | Total Amount | Subtotal over all items, including tax.
amount_paid | Amount paid | Amount paid already.
amount_total_base | Tax Base Total | Base amount for tax calculation.
amount_total_tax | Tax Total | Total tax amount.

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

Attr. rir_field_names | Table
--- | ---
tax_details | Tax details
line_items | Line items


#### Tax details

> Example of a tax details table:
Example of a tax details table:

```
{"category":"section","children":[{"category":"multivalue","children":{"category":"tuple","children":[{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"# ##0.#","id":"vat_detail_rate","label":"VAT rate","rir_field_names":["tax_detail_rate"],"type":"number","width":15},...],"id":"vat_detail","label":"VAT detail"},"default_value":null,"id":"vat_details","label":"VAT details","max_occurrences":null,"min_occurrences":null,"rir_field_names":["tax_details"]}],"icon":null,"id":"amounts_section","label":"Amounts section"}
```

Tax details table and breakdown by tax rates.

Attr. rir_field_names | Field label | Description
--- | --- | ---
tax_detail_base | Tax Base | Sum of tax bases for items with the same tax rate.
tax_detail_rate | Tax Rate | One of the tax rates in the tax breakdown.
tax_detail_tax | Tax Amount | Sum of taxes for items with the same tax rate.
tax_detail_total | Tax Total | Total amount including tax for all items with the same tax rate.
tax_detail_code | Tax Code | [BETA]Text on document describing tax code of the tax rate (e.g. 'GST', 'CGST', 'DPH', 'TVA'). If multiple tax rates belong to one tax code on the document, the tax code will be assigned only to the first tax rate. (in future such tax code will be distributed to all matching tax rates.)


#### Line items

> Example of a line items table:
Example of a line items table:

```
{"category":"section","children":[{"category":"multivalue","children":{"category":"tuple","children":[{"category":"datapoint","constraints":{"required":true},"default_value":null,"id":"item_desc","label":"Description","rir_field_names":["table_column_description"],"type":"string","stretch":true},{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"# ##0.#","id":"item_quantity","label":"Quantity","rir_field_names":["table_column_quantity"],"type":"number","width":15},{"category":"datapoint","constraints":{"required":false},"default_value":null,"format":"# ##0.#","id":"item_amount_total","label":"Price w tax","rir_field_names":["table_column_amount_total"],"type":"number"}],"id":"line_item","label":"Line item","rir_field_names":[]},"default_value":null,"id":"line_items","label":"Line item","max_occurrences":null,"min_occurrences":null,"rir_field_names":["line_items"]}],"icon":null,"id":"line_items_section","label":"Line items"}
```

AI engine currently automatically extracts line item table content and recognizes row and column types as detailed below.
Invoice line items come in a wide variety of different shapes and forms. The current implementation can deal with
(or learn) most layouts, with borders or not, different spacings, header rows, etc. We currently make
two further assumptions:
- The table generally follows a grid structure - that is, columns and rows may be represented as rectangle spans.
In practice, this means that we may currently cut off text that overlaps from one cell to the next column.
We are also not optimizing for table rows that are wrapped to multiple physical lines.
- The table contains just a flat structure of line items, without subsection headers, nested tables, etc.
We plan to gradually remove both assumptions in the future.

Attribute rir_field_names | Field label | Description
--- | --- | ---
table_column_code | Item Code/Id | Can be the SKU, EAN, a custom code (string of letters/numbers) or even just the line number.
table_column_description | Item Description | Line item description. Can be multi-line with details.
table_column_quantity | Item Quantity | Quantity of the item.
table_column_uom | Item Unit of Measure | Unit of measure of the item (kg, container, piece, gallon, ...).
table_column_rate | Item Rate | Tax rate for the line item.
table_column_tax | Item Tax | Tax amount for the line. Rule of thumb:tax = rate * amount_base.
table_column_amount_base | Amount Base | Unit price without tax. (This is the primary unit price extracted.)
table_column_amount | Amount | Unit price with tax. Rule of thumb:amount = amount_base + tax.
table_column_amount_total_base | Amount Total Base | The total amount to be paid for all the items excluding the tax. Rule of thumb:amount_total_base = amount_base * quantity.
table_column_amount_total | Amount Total | The total amount to be paid for all the items including the tax. Rule of thumb:amount_total = amount * quantity.
table_column_other | Other | Unrecognized data type.


# Annotation Lifecycle

When a document is submitted to Rossum within a given queue, anannotation objectis assigned to it.
An annotation goes through a variety of states as it is processed, and eventually exported.

State | Description
--- | ---
created | Annotation was created manually via POST to annotations endpoint. Annotation created this way may be switched toimportingstate only at the end of theupload.createdevent (this happens automatically).
importing | Document is being processed by theAI Enginefor data extraction.
failed_import | Import failed e.g. due to a malformed document file.
split | Annotation was split in user interface or via API and new annotations were created from it.
to_review | Initial extraction step is done and the annotation is waiting for user validation.
reviewing | Annotation is undergoing validation in the user interface.
in_workflow | Annotation is being processed in a workflow. Annotation content cannot be modified while in this state. Please note that any manual interaction with this status may introduce confilicts with Rossum automated workflows. Read more about Rossum Workflowshere.
confirmed | Annotation is validated and confirmed by the user. This status must be explicitly enabled on thequeueto be present.
rejected | Annotation was rejected by user. This status must be explicitly enabled on thequeueto be present. You can read about when a rejection is possiblehere.
exporting | Annotation is validated and is now awaiting the completion of connector save call. Seeconnector extensionfor more information on this status.
exported | Annotation is validated and successfully passed all hooks; this is the typical terminal state of an annotation.
failed_export | When the connector returned an error.
postponed | Operator has chosen to postpone the annotation instead of exporting it.
deleted | When the annotation was deleted by the user.
purged | Only metadata was preserved after a deletion. This status is terminal and cannot be further changed. Seepurge deletedif you want to know how to purge an annotation.

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
> Download usage statistics (January 2019).
Download usage statistics (January 2019).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/annotations/usage_report?from=2019-01-01&to=2019-01-31'
```

Csv file (csv) may be downloaded fromhttps://<example>.rossum.app/api/v1/annotations/usage_report?format=csv.
You may specify date range usingfromandtoparameters (inclusive). If not
specified, a report for last 12 months is generated.

### Request

POST /v1/annotations/usage_report

Attribute | Type | Description
--- | --- | ---
filter | object | Filters to be applied on documents used for the computation of usage report
filter.users | list[URL] | Filter documents modified by the specified users (not applied toimported_count)
filter.queues | list[URL] | Filter documents from the specified queues
filter.begin_date | datetime | Filter documents that has date (arrived_atforimported_count;deleted_atfordeleted_count;rejected_atforrejected_count; orexported_atfor the rest)greaterthan specified.
filter.end_date | datetime | Filter documents that has date (arrived_atforimported_count;deleted_atfordeleted_count;rejected_atforrejected_count; orexported_atfor the rest)lowerthan specified.
exported_on_time_threshold_s | float | Threshold (in seconds) under which are documents denoted ason_time.
group_by | list[string] | List of attributes by which theseriesis to be grouped. Possible values:user,workspace,queue,month,week,day.


```
{"filter":{"users":["https://<example>.rossum.app/api/v1/users/173"],"queues":["https://<example>.rossum.app/api/v1/queues/8199"],"begin_date":"2019-12-01","end_date":"2020-01-31"},"exported_on_time_threshold_s":86400,"group_by":["user","workspace","queue","month"]}
```


### Response


```
{"series":[{"begin_date":"2019-12-01","end_date":"2020-01-01","queue":"https://<example>.rossum.app/api/v1/queues/8199","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","values":{"imported_count":2,"confirmed_count":6,"rejected_count":2,"rejected_automatically_count":1,"rejected_manually_count":1,"deleted_count":null,"exported_count":null,"turnaround_avg_s":null,"corrections_per_document_avg":null,"exported_on_time_count":null,"exported_late_count":null,"time_per_document_avg_s":null,"time_per_document_active_avg_s":null,"time_and_corrections_per_field":[]}},{"begin_date":"2020-01-01","end_date":"2020-02-01","queue":"https://<example>.rossum.app/api/v1/queues/8199","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","user":"https://<example>.rossum.app/api/v1/users/173","values":{"imported_count":null,"confirmed_count":6,"rejected_count":3,"rejected_automatically_count":2,"rejected_manually_count":1,"deleted_count":2,"exported_count":2,"turnaround_avg_s":1341000,"corrections_per_document_avg":1.0,"exported_on_time_count":1,"exported_late_count":1,"time_per_document_avg_s":70.0,"time_per_document_active_avg_s":50.0,"time_and_corrections_per_field":[{"schema_id":"date_due","label":"Date due","total_count":1,"corrected_ratio":0.0,"time_spent_avg_s":0.0},...]}},...],"totals":{"imported_count":7,"confirmed_count":6,"rejected_count":5,"rejected_automatically_count":3,"rejected_manually_count":2,"deleted_count":2,"exported_count":3,"turnaround_avg_s":894000,"corrections_per_document_avg":1.0,"exported_on_time_count":2,"exported_late_count":1,"time_per_document_avg_s":70.0,"time_per_document_active_avg_s":50.0}}
```

The response consists of two parts:totalsandseries.

### Totals

Totalscontain summary information for the whole period (betweenbegin_dateandend_date).

Attribute | Type | Description
--- | --- | ---
imported_count | int | Count of documents that were uploaded to Rossum
confirmed_count | int | Count of documents that were confirmed
rejected_count | int | Count of documents that were rejected
rejected_automatically_count | int | Count of documents that were automatically rejected
rejected_manually_count | int | Count of documents that were manually rejected
deleted_count | int | Count of documents that were deleted
exported_count | int | Count of documents that were successfully exported
turnaround_avg_s | float | Average time (in seconds) that a document spends in Rossum (computed as timeexported_at-arrived_at)
corrections_per_document_avg | float | Average count of corrections on documents
exported_on_time_count | int | Number of documents of whichturnaroundwasunderexported_on_time_threshold
exported_late_count | int | Number of documents of whichturnaroundwasaboveexported_on_time_threshold
time_per_document_avg_s | float | Average time (in seconds) that users spent validating documents. Based on thetime_spent_overallmetric, seeannotation processing duration
time_per_document_active_avg_s | float | Average active time (in seconds) that users spent validating documents. Based on thetime_spent_activemetric, seeannotation processing duration


### Series

Seriescontain information grouped by fields defined ingroup_by.
The data (seeabove) are wrapped invaluesobject,
and accompanied by the values of attributes that were used for grouping.

Attribute | Type | Description
--- | --- | ---
user | URL | User, who modified documents within the group
workspace | URL | Workspace, in which are the documents within the group
queue | URL | Queue, in which are the documents within the group
begin_date | date | Start date, of the documents within the group
end_date | date | Final date, of the documents within the group
values | object | Contains the data oftotalsandtime_and_corrections_per_fieldlist (for details seebelow).

In addition to thetotalsdata,seriescontaintime_and_corrections_per_fieldlist
that provides detailed data about statistics on each field.

#### Series details

The detail object contains statistics grouped per field (schema_id).

Attribute | Type | Description
--- | --- | ---
schema_id | string | Reference mapping of thedata objectto the schema tree
label | string | Label of the data object (taken from schema).
total_count | int | Number of data objects
corrected_ratio* | float [0;1] | Ratio of data objects that must have been corrected after automatic extraction.
time_spent_avg_s | float | Average time (in seconds) spent on validating the data objects

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
- Robust retry mechanism in case of webhook failure
- If webhooks are connected via therun_afterparameter, the results from the predecessor webhook are passed to its successor
Webhooks are defined using ahookobject of typewebhook. For a description
how to create and manage hooks, see theHook API.

### Webhook Events

> Example data sent forannotation_statusevent to thehook.config.urlwhen status of the annotation changes
Example data sent forannotation_statusevent to thehook.config.urlwhen status of the annotation changes

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/789","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"my-rossum-importer","password":"secret-importer-user-password"},"action":"changed","event":"annotation_status","annotation":{"document":"https://<example>.rossum.app/api/v1/documents/314621","id":314521,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/223","pages":["https://<example>.rossum.app/api/v1/pages/551518"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","previous_status":"importing","rir_poll_id":"54f6b91cfb751289e71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/314521","content":"https://<example>.rossum.app/api/v1/annotations/314521/content","time_spent":0,"metadata":{},"organization":"https://<example>.rossum.app/api/v1/organizations/1"},"document":{"id":314621,"url":"https://<example>.rossum.app/api/v1/documents/314621","s3_name":"272c2f41ae84a4f19a422cb432a490bb","mime_type":"application/pdf","arrived_at":"2019-02-06T23:04:00.933658Z","original_file_name":"test_invoice_1.pdf","content":"https://<example>.rossum.app/api/v1/documents/314621/content","metadata":{}}}
```

> Example data sent forannotation_contentevent to thehook.config.urlwhen user updates a value in UI
Example data sent forannotation_contentevent to thehook.config.urlwhen user updates a value in UI

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/781","settings":{"example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"password":"secret-importer-user-password"},"action":"updated","event":"annotation_content","annotation":{"document":"https://<example>.rossum.app/api/v1/documents/314621","id":314521,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/223","pages":["https://<example>.rossum.app/api/v1/pages/551518"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","previous_status":"importing","rir_poll_id":"54f6b91cfb751289e71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/314521","organization":"https://<example>.rossum.app/api/v1/organizations/1","content":[{"id":1123123,"url":"https://<example>.rossum.app/api/v1/annotations/314521/content/1123123","schema_id":"basic_info","category":"section","children":[{"id":20456864,"url":"https://<example>.rossum.app/api/v1/annotations/1/content/20456864","content":{"value":"18 492.48","normalized_value":"18492.48","page":2,...},"category":"datapoint","schema_id":"number","validation_sources":["checks","score"],"time_spent":0}]}],"time_spent":0,"metadata":{}},"document":{"id":314621,"url":"https://<example>.rossum.app/api/v1/documents/314621","s3_name":"272c2f41ae84a4f19a422cb432a490bb","mime_type":"application/pdf","arrived_at":"2019-02-06T23:04:00.933658Z","original_file_name":"test_invoice_1.pdf","content":"https://<example>.rossum.app/api/v1/documents/314621/content","metadata":{}},"updated_datapoints":[11213211,11213212]}
```

> Example of a response forannotation_contenthook
Example of a response forannotation_contenthook

```
{"messages":[{"content":"Invalid invoice number format","id":197467,"type":"error"}],"operations":[{"op":"replace","id":198143,"value":{"content":{"value":"John","position":[103,110,121,122],"page":1},"hidden":false,"options":[],"validation_sources":["human"]}},{"op":"remove","id":884061},{"op":"add","id":884060,"value":[{"schema_id":"item_description","content":{"page":1,"position":[162,852,371,875],"value":"Bottle"}}]}]}
```

> Example data sent foremailevent to thehook.config.urlwhen email is received by Rossum mail server
Example data sent foremailevent to thehook.config.urlwhen email is received by Rossum mail server

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/781","settings":{"example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"password":"secret-importer-user-password"},"action":"received","event":"email","email":"https://<example>.rossum.app/api/v1/emails/987","queue":"https://<example>.rossum.app/api/v1/queues/41","files":[{"id":"1","filename":"image.png","mime_type":"image/png","n_pages":1,"height_px":100.0,"width_px":150.0,"document":"https://<example>.rossum.app/api/v1/documents/427"},{"id":"2","filename":"MS word.docx","mime_type":"application/vnd.openxmlformats-officedocument.wordprocessingml.document","n_pages":1,"height_px":null,"width_px":null,"document":"https://<example>.rossum.app/api/v1/documents/428"},{"id":"3","filename":"A4 pdf.pdf","mime_type":"application/pdf","n_pages":3,"height_px":3510.0,"width_px":2480.0,"document":"https://<example>.rossum.app/api/v1/documents/429"},{"id":"4","filename":"unknown_file","mime_type":"text/xml","n_pages":1,"height_px":null,"width_px":null,"document":"https://<example>.rossum.app/api/v1/documents/430"}],"headers":{"from":"test@example.com","to":"east-west-trading-co-a34f3a@<example>.rossum.app","reply-to":"support@example.com","subject":"Some subject","date":"Mon, 04 May 2020 11:01:32 +0200","message-id":"15909e7e68e4b5f56fd78a3b4263c4765df6cc4d","authentication-results":"example.com;\ndmarc=pass d=example.com"},"body":{"body_text_plain":"Some body","body_text_html":"<div dir=\"ltr\">Some body</div>"}}
```

> Example of a response foremailhook
Example of a response foremailhook

```
{"files":[{"id":"3","values":[{"id":"email:invoice_id","value":"INV001234"},{"id":"email:customer_name","value":"John Doe"}]}],"additional_files":[{"document":"https://<example>.rossum.app/api/v1/documents/987","import_document":true,"values":[{"id":"email:internal_id","value":"0045654"}]}]}
```

> Example data sent forinvocation.scheduledevent and action
Example data sent forinvocation.scheduledevent and action

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/789","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"my-rossum-importer","password":"secret-importer-user-password"},"action":"scheduled","event":"invocation"}
```

> Example data sent foruploadevent to thehook.config.urlwhen documents are uploaded (either through API or as an Email attachment)
Example data sent foruploadevent to thehook.config.urlwhen documents are uploaded (either through API or as an Email attachment)

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/781","settings":{},"secrets":{},"action":"created","event":"upload","email":"https://<example>.rossum.app/api/v1/emails/987","upload":"https://<example>.rossum.app/api/v1/uploads/2046","metadata":{},"files":[{"document":"https://<example>.rossum.app/api/v1/documents/427","prevent_importing":false,"values":[],"queue":"https://<example>.rossum.app/api/v1/queues/41","annotation":null},{"document":"https://<example>.rossum.app/api/v1/documents/428","prevent_importing":true,"values":[],"queue":"https://<example>.rossum.app/api/v1/queues/41","annotation":"https://<example>.rossum.app/api/v1/annotations/1638"}],"documents":[{"id":427,"url":"https://<example>.rossum.app/api/v1/documents/427","mime_type":"application/pdf",...},{"id":428,"url":"https://<example>.rossum.app/api/v1/documents/428","mime_type":"application/json",...}]}
```

> Example of a response forupload.createdhook
Example of a response forupload.createdhook

```
{"files":[{"document":"https://<example>.rossum.app/api/v1/documents/427","prevent_importing":false,"messages":[{"type":"error","content":"Some error message."}]},{"document":"https://<example>.rossum.app/api/v1/documents/428","prevent_importing":true},{"document":"https://<example>.rossum.app/api/v1/documents/429",},{"document":"https://<example>.rossum.app/api/v1/documents/430","messages":[{"type":"info","content":"Some info message."}]}]}
```

Webhook events specify when the hook should be notified. They can be defined as following:
- either as whole event containing all supported actions for its type (for exampleannotation_status)
- or as separately named actions for specified event (for exampleannotation_status.changed)

#### Supported events and their actions


Event and Action | Payload (outside default attributes) | Response | Description | Retry on failure
--- | --- | --- | --- | ---
annotation_status.changed | annotation, document | N/A | Annotationstatuschange occurred | yes
annotation_content.initialize | annotation + content, document, updated_datapoints | operations, messages | Annotation was initialized (data extracted) | yes
annotation_content.started | annotation + content, document, updated_datapoints (empty) | operations, messages | User entered validation screen | no (interactive)
annotation_content.user_update | annotation + content, document, updated_datapoints | operations, messages | (Deprecated in favor ofannotation_content.updated) Annotation was updated by the user | no (interactive)
annotation_content.updated | annotation + content, document, updated_datapoints | operations, messages | Annotation data was updated by the user | no (interactive)
annotation_content.confirm | annotation + content, document, updated_datapoints (empty) | operations, messages | User confirmed validation screen | no (interactive)
annotation_content.export | annotation + content, document, updated_datapoints (empty) | operations, messages | Annotation is being moved to exported state | yes
upload.created | files, documents, metadata, email, upload | files | Upload object was created | yes
email.received | files, headers, body, email, queue | files (*) | Email with attachments was received | yes
invocation.scheduled | N/A | N/A | Hook was invoked at the scheduled time | yes
invocation.manual | custom payload fields | forwarded hook response | Event formanual hook triggering | no

(*) May also contain other optional attributes - read more inthis section.
- Whenannotation_content.exportaction fails, annotation is switched to thefailed_exportstate.
- Whenresponse from webhookonannotation_content.exportcontains a message of typeerror, the annotation is switched to thefailed_exportstate.
- Theupdated_datapointslist is never empty forannotation_content.updatedonly triggered by interactive date changes actions.
- Theupdated_datapointslist is always empty for theannotation_content.exportaction.
- Theupdated_datapointslist is empty for theannotation_content.initializeaction ifrun_after=[], but it can have data from its predecessor if chained viarun_after.
- Theupdated_datapointslist may also be empty forannotation_content.user_updatein case of an action triggered interactively by a user, but with no data changes (e.g. after opening validation screen or eventually at its confirmation issued by the Rossum UI).
- For each webhook call there is a 30 seconds timeout by default (this applies to all events and actions).
It can be modified inconfigwith attributetimeout_s(min=0, max=60, only for non-interactive webhooks).
- In case a non-interactive webhook call fails (check the configuration ofretry_on_any_non_2xxattribute
of thewebhookto see what statuses this includes), it is retried within 30 seconds by default.
There are up to 5 attempts performed. This number can be modified inconfigwith attributeretry_count(min=0, max=4, only for non-interactive webhooks).
Non-interactive webhooks can use also asynchronous framework:
- Webhook returns an HTTP status 202 and url for polling in the responseLocationheader.
- The provided polling url is polled every 30 seconds until a response with 201 status code is received. The response
body is then taken as the hook call result.
- The polling continues until 201 response is received or until the maximum polling time is exceeded. See
themax_polling_time_sattribute of thehook.configfor more details.
- In case the polling request returns one of the following status codes:408, 429, 500, 502, 503, 504, it is retried
and the polling continues. (This is not considered a polling failure.)
- In case the polling request fails (returns any error status code other than408, 429, 500, 502, 503, 504or exceeds
the maximum polling time), the original webhook call is retried (by default). The number of retry attempts is set by
theretry_countattribute of thehook.config.
- Retries after polling can be enabled/disabled by theretry_after_polling_failureattribute of thehook.config.
To show an overview of the Hook events and when they are happening, this diagram was created.

#### Hooks common attributes


Key | Type | Description
--- | --- | ---
request_id | UUID | Hookcall request ID
timestamp | datetime | Timestamp when thehookwas called
hook | URL | Hook's url
action | string | Hook'saction
event | string | Hook'sevent
settings | object | Copy ofhook.settingsattribute


#### Annotation status event data format

annotation_statusevent contains following additional event specific attributes.

Key | Type | Description
--- | --- | ---
annotation | object | Annotation object (enriched with attributeprevious_status)
document | object | Document object (attributeannotationsis excluded)
queues* | list[object] | list of relatedqueueobjects
modifiers* | list[object] | list of relatedmodifierobjects
schemas* | list[object] | list of relatedschemaobjects
emails* | list[object] | list of relatedemailobjects (for annotations created after email ingestion)
related_emails* | list[object] | list of relatedemailsobjects (other related emails)
relations* | list[object] | list of relatedrelationobjects
child_relations* | list[object] | list of relatedchild_relationobjects
suggested_edits* | list[object] | list of relatedsuggested_editsobjects
assignees* | list[object] | list of relatedassigneeobjects
pages* | list[object] | list of relatedpagesobjects
notes* | list[object] | list of relatednotesobjects
labels* | list[object] | list of relatedlabelsobjects
automation_blockers* | list[object] | list of relatedautomation_blockersobjects

*Attribute is only included in the request when specified inhook.sideload. Please note that sideloading of modifier object from different organization is not supported and that sideloading can decrease performance. See alsoannotationsideloading section.
> Example data sent to hook with sideloadedqueueobjects
Example data sent to hook with sideloadedqueueobjects

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5214b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","hook":"https://<example>.rossum.app/api/v1/hooks/781","action":"changed","event":"annotation_status",...,"queues":[{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198",...,"metadata":{},"use_confirmed_state":false,"settings":{}}]}
```


#### Annotation content event data format

annotation_contentevent contains following additional event specific attributes.

Key | Type | Description
--- | --- | ---
annotation | object | Annotation object. Content is pre-loaded withannotation data. Annotation data are enriched withnormalized_value, see example.
document | object | Document object (attributeannotationsis excluded)
updated_datapoints** | list[int] | List of IDs of datapoints that were changed by last or all predecessor events.
queues* | list[object] | list of relatedqueueobjects
modifiers* | list[object] | list of relatedmodifierobjects
schemas* | list[object] | list of relatedschemaobjects
emails* | list[object] | list of relatedemailobjects (for annotations created after email ingestion)
related_emails* | list[object] | list of relatedemailsobjects (other related emails)
relations* | list[object] | list of relatedrelationobjects
child_relations* | list[object] | list of relatedchild_relationobjects
suggested_edits* | list[object] | list of relatedsuggested_editsobjects
assignees* | list[object] | list of relatedassigneeobjects
pages* | list[object] | list of relatedpagesobjects
notes* | list[object] | list of relatednotesobjects
labels* | list[object] | list of relatedlabelsobjects
automation_blockers* | list[object] | list of relatedautomation_blockersobjects

*Attribute is only included in the request when specified inhook.sideload. Please note that sideloading of modifier object from different organization is not supported and that sideloading can decrease performance. See alsoannotationsideloading section.
**If therun_afterattribute chains the hooks, the updated_datapoints will contain a list of all datapoint ids that were updated by any of the predecessive hooks. Moreover, in case ofaddoperation on a multivalue table, theupdated_datapointswill contain theidof the multivalue, theidof the new tuple datapoints and theidof all the newly created cell datapoints.

#### Annotation content event response format

All of theannotation_contentevents expect a JSON object with the following
optional lists in the response:messagesandoperations
Themessageobject contains attributes:

Key | Type | Description
--- | --- | ---
id | integer | Optional unique id of the relevant datapoint; omit for a document-wide issues
type | enum | One of:error,warningorinfo.
content | string | A descriptive message to be shown to the user
detail | object | Detail object that enhances the response from a hook. (For more info refer tomessage detail)

For example, you may useerrorfor fatals like a missing required field,
whereasinfois suitable to decorate a supplier company id with its name as
looked up in the supplier's database.
Theoperationsobject describes operation to be performed on the annotation
data (replace,add,remove). Format of theoperationskey is the same as for
bulk update of annotations, please refer to theannotation
dataAPI for complete description.
It's possible to use the same format even with non-2XX response codes. In this type of response,operationsare not considered.
> Example of a parsable error response
Example of a parsable error response

```
{"messages":[{"id":"all","type":"error","content":"custom error message to be displayed in the UI"}]}
```

initializeevent ofannotation_contentaction additionally accepts list ofautomation_blockersobjects.
This allows for manual creation ofautomation blockersoftypeextensionand therefore stops theautomationwithout the need to create an error message.
Theautomation_blockersobject contains attributes

Key | Type | Description
--- | --- | ---
id | integer | Optional unique id of the relevant datapoint; omit for a document-wide issues
content | str | A descriptive message to be stored as anautomation blocker

> Example of a response forannotation_content.initializehook creating automation blockers
Example of a response forannotation_content.initializehook creating automation blockers

```
{"messages":[...],"operations":[...],"automation_blockers":[{"id":1357,"content":"Unregistered vendor"},{"content":"PO not found in the master data!"}]}
```


#### Email received event data format

emailevent contains following additional event specific attributes.

Key | Type | Description
--- | --- | ---
files | list[object] | List of objects with metadata of each attachment contained in the arriving email.
headers | object | Headers extracted from the arriving email.
body | object | Body extracted from the arriving email.
email | URL | URL of the arriving email.
queue | URL | URL of the arriving email's queue.

Thefilesobject contains attributes:

Key | Type | Description
--- | --- | ---
id | string | Some arbitrary identifier.
filename | string | Name of the attachment.
mime_type | string | MIME typeof the attachment.
n_pages | integer | Number of pages (defaults to 1 if it could not be acquired).
height_px | float | Height in pixels (300 DPI is assumed for PDF files, defaults tonullif it could not be acquired).
width_px | float | Width in pixels (300 DPI is assumed for PDF files, defaults tonullif it could not be acquired).
document | URL | URL of related document object.

Theheadersobject contains the same values as are available forinitialization of valuesinemail_header:<id>(namely:from,to,reply-to,subject,message-id,date).
Thebodyobject contains thebody_text_plainandbody_text_html.

#### Email received event response format

All of theemailevents expect a JSON object with the following lists in the response:files,additional_files,extracted_original_sender
Thefilesobject contains attributes:

Key | Type | Description
--- | --- | ---
id | int | idof file that will be used for creating anannotation
values | list[object] | This is used to initialize datapoint values. Seevaluesobject description below

Thevaluesobject consists of the following:

Key | Type | Description
--- | --- | ---
id | string | Id of value - must start withemail:prefix (to use this value refer to it inrir_field_namesfield in the schema similarly as describedhere).
value | string | String value to be used when annotation content is being constructed

This is useful for filtering out unwanted files by some measures that are not available in Rossum by default.
Theadditional_filesobject contains attributes:

Key | Type | Default | Required | Description
--- | --- | --- | --- | ---
document | URL |  | yes | URL of the document object that should be included. If document belongs to an annotation it must also belong to the same queue as email inbox.
values | list[object] | [] | no | This is used to initialize datapoint values. Seevaluesobject description above
import_document | bool | false | no | Set totrueif Rossum should import document and create an annotation for it, otherwise it will be just linked as an email attachment. Only applicable if document hasn't already an annotation attached.

Theextracted_original_senderobject looks as follows:

Key | Type | Description
--- | --- | ---
extracted_original_sender | email_address_object | Information about sender containing keysemailandname.

This is useful for updating the email address field on email object with a new sender name and email address.

#### Upload created event data format

uploadevent contains following additional event specific attributes.

Key | Type | Description
--- | --- | ---
files | list[object] | List of objects with metadata of each uploaded document.
documents | list[object] | List of document objects corresponding with the files object.
upload | object | Object representing the upload.
metadata | object | Client data passed in through the upload resource to create annotations with.
email | URL | URL of the arriving email ornullif the document was uploaded via API.

Thefilesobject contains attributes:

Key | Type | Description
--- | --- | ---
document | URL | URL of the uploaded document object.
prevent_importing | bool | If set no annotation is going to be created for the document or if already existing it is not going to be switched toimportingstatus.
values | list[object] | This is used to initialize datapoint values. Seevaluesobject description below
queue | URL | URL of the queue the document is being uploaded to.
annotation | URL | URL of the documents annotation ornullif it doesn't exist.

Thevaluesobject consists of the following:

Key | Type | Description
--- | --- | ---
id | string | Id of value (to use this value refer to it inrir_field_namesfield in the schema similarly as describedhere).
value | string | String value to be used when annotation content is being constructed


#### Upload created event response format

All of theuploadevents expect a JSON object with thefilesobject list in the response.
Thefilesobject contains attributes:

Key | Type | Description | Required
--- | --- | --- | ---
document | URL | URL of the uploaded document object. | true
prevent_importing | bool | If set no annotation is going to be created for the document or if already exists it is not going to be switched toimportingstatus. Optional, default false. | false
messages | list[object] | List ofmessagesthat will be appended to the related annotation. | false


### Validating payloads from Rossum

> Example of hook receiver, which verifies the validity of Rossum request
Example of hook receiver, which verifies the validity of Rossum request

```
importhashlibimporthmacfromflaskimportFlask,request,abortapp=Flask(__name__)SECRET_KEY="<Your secret key stored in hook.config.secret>"# never store this in code@app.route("/test_hook",methods=["POST"])deftest_hook():digest=hmac.new(SECRET_KEY.encode(),request.data,hashlib.sha256).hexdigest()try:prefix,signature=request.headers["X-Rossum-Signature-SHA256"].split("=")exceptValueError:abort(401,"Incorrect header format")ifnot(prefix=="sha256"andhmac.compare_digest(signature,digest)):abort(401,"Authorization failed.")return
```

For authorization of payloads, theshared secretmethod is used.
When a secret token is set inhook.config.secret, Rossum uses it to create a hash signature with each payload.
This hash signature is passed along with each request in the headers asX-Rossum-Signature-SHA256.
The goal is to compute a hash usinghook.config.secretand the request body,
and ensure that the signature produced by Rossum is the same. Rossum uses HMAC SHA256 signature by default.
Previously, Rossum was using SHA1 algorithm to sign the payload. This option is
still available as a legacyX-Elis-Signatureheader. Please contact
Rossum support to enable this header in case it is missing.
Webhook requests may also be authenticated using a client SSL certificate, seeHookAPI for reference.

### Access to Rossum API

You can access Rossum API from the Webhook. Each execution gets unique API key. The key is valid
for 10 minutes or until Rossum receives a response from the Webhook. You can settoken_lifetime_sup to 2 hours to keep
the token valid longer. The API key and the environment's base URL are passed to webhooks as a first-level attributesrossum_authorization_tokenandbase_urlwithin the webhook payload.

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

Name | Identifier | Deprecation date | Block function creation date | Removal date | Note
--- | --- | --- | --- | --- | ---
Python 3.12 | python3.12 | not scheduled | not scheduled | not scheduled | 
NodeJS 22 | nodejs22.x | not scheduled | not scheduled | not scheduled | 


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

### Implementation

> Example serverless function usable forannotation_contentevent (Python implementation).
Example serverless function usable forannotation_contentevent (Python implementation).

```
'''
This custom serverless function example demonstrates showing messages to the
user on the validation screen, updating values of specific fields, and
executing actions on the annotation.

See https://elis.rossum.ai/api/docs/#rossum-transaction-scripts for more examples.
'''fromtxscriptimportTxScript,default_to,substitutedefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)forrowint.field.line_items:ifdefault_to(row.item_amount_base,0)>=1000000:t.show_warning('Value is too big',row.item_amount_base)# Remove dashes from document_id# Note: This type of operation is strongly discouraged in serverless# functions, since the modification is non-transparent to the user and# it is hard to trace down which hook modified the field.# Always prefer making a formula field!t.field.document_id=substitute(r'-','',t.field.document_id)ifdefault_to(t.field.amount_total,0)>1000000:print("postponing")t.annotation.action("postpone")returnt.hook_response()returnt.hook_response()
```

> Example serverless function usable forannotation_contentevent (JavaScript/NodeJS implementation).
Example serverless function usable forannotation_contentevent (JavaScript/NodeJS implementation).

```
// This serverless function example can be used for annotation_content events// (e.g. updated action). annotation_content events provide annotation// content tree as the input.//// The function below shows how to:// 1. Display a warning message to the user if "item_amount_base" field of//    a line item exceeds a predefined threshold// 2. Removes all dashes from the "invoice_id" field//// item_amount_base and invoice_id should be fields defined in a schema.// --- ROSSUM HOOK REQUEST HANDLER ---// The rossum_hook_request_handler is an mandatory main function that accepts// input and produces output of the rossum serverless function hook.// @param {Object} payload - see https://example.rossum.app/api/docs/#annotation-content-event-data-format// @returns {Object} - the messages and operations that update the annotation contentexports.rossum_hook_request_handler=async(payload)=>{constcontent=payload.annotation.content;try{// Values over the threshold trigger a warning messageconstTOO_BIG_THRESHOLD=1000000;// List of all datapoints of item_amount_base schema idconstamountBaseColumnDatapoints=findBySchemaId(content,'item_amount_base',);constmessages=[];for(vari=0;i<amountBaseColumnDatapoints.length;i++){// Use normalized_value for comparing values of Date and Number fields (https://example.rossum.app/api/docs/#content-object)if(amountBaseColumnDatapoints[i].content.normalized_value>=TOO_BIG_THRESHOLD){messages.push(createMessage('warning','Value is too big',amountBaseColumnDatapoints[i].id,),);}}// There should be only one datapoint of invoice_id schema idconst[invoiceIdDatapoint]=findBySchemaId(content,'invoice_id');// "Replace" operation is returned to update the invoice_id valueconstoperations=[createReplaceOperation(invoiceIdDatapoint,invoiceIdDatapoint.content.value.replace(/-/g,''),),];// Return messages and operations to be used to update current annotation datareturn{messages,operations,};}catch(e){// In case of exception, create and return error message. This may be useful for debugging.constmessages=[createMessage('error','Serverless Function:'+e.message)];return{messages,};}};// --- HELPER FUNCTIONS ---// Return datapoints matching a schema id.// @param {Object} content - the annotation content tree (see https://example.rossum.app/api/docs/#annotation-data)// @param {string} schemaId - the field's ID as defined in the extraction schema(see https://example.rossum.app/api/docs/#document-schema)// @returns {Array} - the list of datapoints matching the schema IDconstfindBySchemaId=(content,schemaId)=>content.reduce((results,dp)=>dp.schema_id===schemaId?[...results,dp]:dp.children?[...results,...findBySchemaId(dp.children,schemaId)]:results,[],);// Create a message which will be shown to the user// @param {number} datapointId - the id of the datapoint where the message will appear (null for "global" messages).// @param {String} messageType - the type of the message, any of {info|warning|error}. Errors prevent confirmation in the UI.// @param {String} messageContent - the message shown to the user// @returns {Object} - the JSON message definition (see https://example.rossum.app/api/docs/#annotation-content-event-response-format)constcreateMessage=(type,content,datapointId=null)=>({content:content,type:type,id:datapointId,});// Replace the value of the datapoint with a new value.// @param {Object} datapoint - the content of the datapoint// @param {string} - the new value of the datapoint// @return {Object} - the JSON replace operation definition (see https://example.rossum.app/api/docs/#annotation-content-event-response-format)constcreateReplaceOperation=(datapoint,newValue)=>({op:'replace',id:datapoint.id,value:{content:{value:newValue,},},});
```

To implement a serverless function, create ahookobject of typefunction. Usecodeobject config attribute to specify a serialized source
code. You can use a code editor built-in to the Rossum UI, which also allows to
test and debug the function before updating the code of the function itself.
See Python and NodeJS examples of a serverless function implementation next to this section
or check outthis article(and
others in the relevant section).
If there is an issue with an extension code itself, it will be displayed asCallFunctionExceptionin the
annotation view. Raising this exception usually means issues such as:
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
> Python code snippet to access Rossum API to get a list of queue names
Python code snippet to access Rossum API to get a list of queue names

```
importjsonimporturllib.requestdefrossum_hook_request_handler(payload):request=urllib.request.Request("https://<example>.rossum.app/api/v1/queues",headers={"Authorization":"Bearer "+payload["rossum_authorization_token"]})withurllib.request.urlopen(request)asresponse:queues=json.loads(response.read())queue_names=(q["name"]forqinqueues["results"])return{"messages":[{"type":"info","content":", ".join(queue_names)}]}
```

> NodeJS code snippet to access Rossum API to get a list of queue names
NodeJS code snippet to access Rossum API to get a list of queue names

```
exports.rossum_hook_request_handler=async(payload)=>{consttoken=payload.rossum_authorization_token;queues=JSON.parse(awaitgetFromRossumApi("https://<example>.rossum.app/api/v1/queues",token));queue_names=queues.results.map(q=>q.name).join(",")return{"messages":[{"type":"info","content":queue_names}]};}constgetFromRossumApi=async(url,token)=>{varhttp=require('http');constproxy=newURL(process.env.HTTPS_PROXY);constoptions={hostname:proxy.hostname,port:proxy.port,path:url,method:'GET',headers:{'Authorization':'token'+token,},};constresponse=awaitnewPromise((resolve,reject)=>{letdataString='';constreq=http.request(options,function(res){res.on('data',chunk=>{dataString+=chunk;});res.on('end',()=>{resolve({statusCode:200,body:dataString});});});req.on('error',(e)=>{reject({statusCode:500,body:'Something went wrong!'});});req.end()});returnresponse.body}
```


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
> Example of a valid no-op (empty)validateresponse
Example of a valid no-op (empty)validateresponse

```
{"messages":[],"updated_datapoints":[]}
```

> Example of a valid no-op (empty)saveresponse
Example of a valid no-op (empty)saveresponse

```
{}
```

The connector API consists of two endpoints,validateandsave,
described below.
A connector must always implement both endpoints (though they may not necessarily
perform a function in a particular connector - see the right column for an empty
reply example), the platform raises an error if it is not able to run an endpoint.
- run on HTTPS and have a valid public certificatebe fast enough to keep up the pace with Rossum interactive behaviorbe able to receive traffic from any IP address. (Source IP address may change over time.)require authentication by authentication token to prevent data leaks or forgery

### Setup a connector

The next step after implementing the first version of a connector is configuring it
in the Rossum platform.
In Rossum, aconnector objectdefinesservice_urlandparamsfor
construction of HTTPS requests andauthorization_tokenthat is passed in
every request to authenticate the caller as the actual Rossum server. It may also
uniquely identify the organization when multiple Rossum organizations share the
same connector server.
To set up a connector for aqueue, create aconnector objectusing either our API or
therossumtool
–follow these instructions.
A connector object may be associated with one or more queues. One queue can only have one connector object associated with it.

### Connector API

> Example data sent to connector (validate,save)
Example data sent to connector (validate,save)

```
{"meta":{"document_url":"https://<example>.rossum.app/api/v1/documents/6780","arrived_at":"2019-01-30T07:55:13.208304Z","original_file":"https://<example>.rossum.app/api/v1/original/bf0db41937df8525aa7f3f9b18a562f3","original_filename":"Invoice.pdf","queue_name":"Invoices","workspace_name":"EU","organization_name":"East West Trading Co","annotation":"https://<example>.rossum.app/api/v1/annotations/4710","queue":"https://<example>.rossum.app/api/v1/queues/63","workspace":"https://<example>.rossum.app/api/v1/workspaces/62","organization":"https://<example>.rossum.app/api/v1/organizations/1","modifier":"https://<example>.rossum.app/api/v1/users/27","updated_datapoint_ids":["197468"],"modifier_metadata":{},"queue_metadata":{},"annotation_metadata":{},"rir_poll_id":"54f6b9ecfa751789f71ddf12","automated":false},"content":[{"id":"197466","category":"section","schema_id":"invoice_info_section","children":[{"id":"197467","category":"datapoint","schema_id":"invoice_number","page":1,"position":[916,168,1190,222],"rir_position":[916,168,1190,222],"rir_confidence":0.97657,"value":"FV103828806S","validation_sources":["score"],"type":"string"},{"id":"197468","category":"datapoint","schema_id":"date_due","page":1,"position":[938,618,1000,654],"rir_position":[940,618,1020,655],"rir_confidence":0.98279,"value":"12/22/2018","validation_sources":["score"],"type":"date"},{"id":"197469","category":"datapoint","schema_id":"amount_due","page":1,"position":[1134,1050,1190,1080],"rir_position":[1134,1050,1190,1080],"rir_confidence":0.74237,"value":"55.20","validation_sources":["human"],"type":"number"}]},{"id":"197500","category":"section","schema_id":"line_items_section","children":[{"id":"197501","category":"multivalue","schema_id":"line_items","children":[{"id":"198139","category":"tuple","schema_id":"line_item","children":[{"id":"198140","category":"datapoint","schema_id":"item_desc","page":1,"position":[173,883,395,904],"rir_position":null,"rir_confidence":null,"value":"Red Rose","validation_sources":[],"type":"string"},{"id":"198142","category":"datapoint","schema_id":"item_net_unit_price","page":1,"position":[714,846,768,870],"rir_position":null,"rir_confidence":null,"value":"1532.02","validation_sources":["human"],"type":"number"}]}]}]}]}
```

All connector endpoints, representing particular points in the
document lifetime, are simple verbs that receive a JSONPOSTed and
potentially expect a JSON returned in turn.
The authorization type and authorization token is passed as anAuthorizationHTTP header. Authorization type may besecret_key(shared secret) orBasicforHTTP basic authentication.
Please note that for Basic authentication,authorization_tokenis passed
as-is, therefore it must be set to a correct base64 encoded value. For example
usernameconnectorand passwordsecure123is encoded asY29ubmVjdG9yOnNlY3VyZTEyMw==authorization token.
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
The metadata identify the concerned document, containing attributes:

Key | Type | Description
--- | --- | ---
document_url | URL | documentURL
arrived_at | timestamp | A time of document arrival in Rossum (ISO 8601)
original_file | URL | Permanent URL for the documentoriginal file
original_filename | string | Filename of the document on arrival in Rossum
queue_name | string | Name of the document's queue
workspace_name | string | Name of the document's workspace
organization_name | string | Name of the document's organization
annotation | URL | Annotation URL
queue | URL | Document's queue URL
workspace | URL | Document's workspace URL
organization | URL | Document's organization URL
modifier | URL | Modifier URL
modifier_metadata | object | Metadata attribute of the modifier, seemetadata
queue_metadata | object | Metadata attribute of the queue, seemetadata
annotation_metadata | object | Metadata attribute of the annotation, seemetadata
rir_poll_id | string | Internal extractor processing id
updated_datapoint_ids | list[string] | Ids of objects that were recently modified by user
automated | bool | Flag whether annotation wasautomated

A common class of content is theannotation tree, which is a JSON object
that can contain nested datapoint objects, and matches the schema datapoint tree.
Intermediate nodes have the following structure:

Key | Type | Description
--- | --- | ---
id | integer | A unique id of the given node
schema_id | string | Reference mapping the node to the schema tree
category | string | One ofsection,multivalue,tuple
children | list | A list of other nodes

Datapoint (leaf) nodes structure contains actual data:

Key | Type | Description
--- | --- | ---
id | integer | A unique id of the given node
schema_id | string | Reference mapping the node to the schema tree
category | string | datapoint
type | string | One ofstring,dateornumber, as specified in theschema
value | string | The datapoint value, string represented but normalizes, to that they are machine readable: ISO format for dates, a decimal for numbers
page | integer | A 1-based integer index of the page, optional
position | list[float] | List of four floats describing the x1, y1, x2, y2 bounding box coordinates
rir_position | list[float] | Bounding box of the value as detected by the data extractor. Format is the same as forposition.
rir_confidence | float | Confidence (estimated probability) that this field was extracted correctly.


#### Annotation lifecycle with a connector

If an asynchronous connector is deployed to a queue, an annotation status will change fromreviewingtoexportingand subsequently toexportedorfailed_export. If no connector extension is deployed to a queue or if the attributeasynchronousis set tofalse, an annotation status will change fromreviewingtoexported(orfailed_export) directly.

### Endpoint: validate

This endpoint is called after the document processing has finished, when operator opens a document
in the Rossum verification interface and then every time after operator updates a field. After the
processing is finished, the initial validate call is marked withinitial=trueURL parameter.
For the other calls, only/validatewithout the parameter is called. Note that after document processing, initial 
validation is followed bybusiness rulesexecution for bothvalidationandannotation_importedevents.
The request path is fixed to/validateand cannot be changed.
- validate the given annotation tree and return a list of messages commenting on it
(e.g. pointing out errors or showing matched suppliers).
- update the annotation tree by returning a list of replace, add and remove operations
Both the messages and the updated data are shown in the verification
interface. Moreover, the messages may block confirmation in the case of errors.
This endpoint should be fast as it is part of an interactive workflow.
Receives an annotation tree ascontent.
Returns a JSON object with the lists:messages,operationsandupdated_datapoints.

#### Keysmessages,operations(optional)

The description of these keys was moved to theHook Extension. See the descriptionhere.

#### Keyupdated_datapoints(optional, deprecated)

We also support a simplified version of updates usingupdated_datapointsresponse key. It only supports updates (no add or remove operations) and is now
deprecated. The updated datapoint object contains attributes:

Key | Type | Description
--- | --- | ---
id | string | A unique id of the relevant datapoint, currently only datapoints of categorydatapointcan be updated
value | string | New value of the datapoint. Value is formatted according to the datapoint type (e.g. date is string representation of ISO 8601 format).
hidden | boolean | Toggle for hiding/showing of the datapoint, seedatapoint
options | list[object] | Options of the datapoint -- valid only fortype=enum, seeenum options
position | list[float] | New position of the datapoint, list of four numbers.

Validate endpoint should always return200 OKstatus.
Anerrormessage returned from the connector prevents user from confirming the document.

### Endpoint: save

This endpoint is called when the invoice transitions to theexportedstate.
Connector may process the final document annotation and save it to the target
system. It receives an annotation tree ascontent. The request path is fixed
to/saveand cannot be changed.
The save endpoint is called asynchronously (unless synchronous mode is set) in
relatedconnector object. Timeout of the save endpoint is 60
seconds.
For successful export, the request should have2xxstatus.
> Example of successfulsaveresponse without messages in UI
Example of successfulsaveresponse without messages in UI

```
HTTP/1.1204No Content
```


```
HTTP/1.1200OKContent-Type:text/plainthis response body is ignored
```


```
HTTP/1.1200OKContent-Type:application/json{"messages":[]}
```

When messages are expected to be displayed in the UI, they should be sent in the
same format as invalidate endpoint.
> Example of successfulsaveresponsewithmessages in UI
Example of successfulsaveresponsewithmessages in UI

```
HTTP/1.1200OKContent-Type:application/json{"messages":[{"content":"Everything is OK.","id":null,"type":"info"}]}
```

If the endpoint fails with an HTTP error and/or message of typeerroris received,
the document transitions to thefailed_exportstate - it is then available
to the operators for manual review and re-queuing to theto_reviewstate
in the user interface. Re-queuing may be done also programmatically via
the API using a PATCH call to setto_reviewannotation status. Patching
annotation status toexportingstate triggers an export retry.
> Example of unsuccessfulsaveresponsewithmessages in UI
Example of unsuccessfulsaveresponsewithmessages in UI

```
HTTP/1.1422Unprocessable EntityContent-Type:application/json{"messages":[{"content":"Even though this message is info, the export will fail due to the status code.","id":null,"type":"info"}]}
```


```
HTTP/1.1500Internal Server ErrorContent-Type:text/plainAn errror message "Export failed." will show up in the UI
```


```
HTTP/1.1200OKContent-Type:application/json{"messages":[{"content":"Proper status code could not be set.","id":null,"type":"error"}]}
```


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

The shape of theresultkey is the same as the top levelcontentattribute of theannotation dataresponse.
Once the listener is in place, you can post one of supported message types:
- GET_DATAPOINTS- returns the same tree structure you’d get by requesting annotation data

```
window.opener.postMessage({type:'GET_DATAPOINTS'},'https://<example>.rossum.app')
```

- UPDATE_DATAPOINT- sends updated value to a Rossum datapoint. Only one datapoint value can be updated
at a time.

```
window.opener.postMessage({type:'UPDATE_DATAPOINT',data:{id:DATAPOINT_ID,value:"Updated value"}},'https://<example>.rossum.app')
```

- FINISH- informs the Rossum app that the popup process is ready to be closed.
After this message is posted, popup will be closed and Rossum app will trigger a validate call.

```
window.opener.postMessage({type:'FINISH'},'https://<example>.rossum.app');
```

Providing message type to postMessage lets Rossum interface know what operation
user requests and determines the type of the answer which could be used to
match appropriate response.

#### Validate button

Ifpopup_urlkey is missing in button’s schema, clicking the button will trigger a standard validate call to connector. In such call,updated_datapoint_idswill contain the ID of the pressed button.
Note: if you’re missing some annotation data that you’d like to receive in a similar way, do contact our support team. We’re collecting feedback to further expand this list.

## Extension Logs

For easy and efficient development process of the extensions, our backend logsrequests,responses(if enabled) and
additional information, when the hook is being called.

### Hook Log

The hook log objects consist of following attributes, where it also differentiates between the hook events as follows:

#### Base Hook Log object

These attributes are included in all the logs independent of the hook event

Key | Type | Description | Optional
--- | --- | --- | ---
timestamp* | str | Timestamp of the log-record | 
request_id | UUID | Hookcall request ID | 
event | string | Hook'sevent | 
action | string | Hook'saction | 
organization_id | int | ID of the associatedOrganization. | 
queue_id | int | ID of the associatedQueue. | true
hook_id | int | ID of the associatedHook. | 
hook_type | str | Hook type. Possible values:webhook,function | 
log_level | str | Log-level. Possible values:INFO,ERROR,WARNING | 
message | str | A log-message | 
request | str | Raw request sent to the Hook | true
response | str | Raw response received from the Hook | true

*Timestamp is of the ISO 8601 format with UTC timezone e.g.2023-04-21T07:58:49.312655

#### Annotation Content or Annotation Status Hook Events

In addition to the Base Hook Log object, theannotation contentandannotation statusevent hook logs contains
the following attributes:

Key | Type | Description | Optional
--- | --- | --- | ---
annotation_id | int | ID of the associatedAnnotation. | true


#### Email Hook Events

In addition to the Base Hook Log object, theemailevent hook logs contains the following attributes:

Key | Type | Description | Optional
--- | --- | --- | ---
email_id | int | ID of the associatedEmail. | true


## Source IP Address ranges

Rossum will use these source IP addresses for outgoing connections to your
services (e.g. when sending requests to a webhook URL):
- 34.254.110.123
- 52.209.175.153
- 54.217.193.239
- 54.246.127.143
Europe 2 (Frankfurt):
- 3.75.26.254
- 3.126.211.68
- 3.126.98.96
- 3.76.159.143
- 3.222.161.192
- 50.19.104.88
- 52.2.120.212
- 18.213.174.191
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
The TxScript Python environment is based on Python 3.12 or newer,
in addition including a variety of additional predefined functions and variables.
The environment has been designed so that code operating on Rossum objects
is very short, easy to read and write by both humans and LLMs, and many simple
tasks are doable even by non-programmers (who could however e.g. build
an Excel spreadsheet).
The environment is special in the following ways:
- Predefined variables allowing easy access to Rossum objects.
- Some environment-specific helper functions and aliases.
- How code is evaluated specifically in formula field context to yield a computed value.
Predefined variables allowing easy access to Rossum objects.
Some environment-specific helper functions and aliases.
How code is evaluated specifically in formula field context to yield a computed value.
The TxScript environment provides accessors to Rossum objects associated with
the event that triggered the code evaluation.
The event context is generally available through atxscript.TxScriptobject;
calling the object methods and modifying the attributes (such as raising
messages or modifying field values) controls the event hook response.
> Example of a no-op serverless function instantiating theTxScriptobject
Example of a no-op serverless function instantiating theTxScriptobject

```
fromtxscriptimportTxScriptdefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)print(t)returnt.hook_response()
```

In serverless functions,
this object must be explicitly imported and instantiated using a.from_payload()function.  The.hook_response()method yields a dict representing the
prescribed event hook response (with keys such as"messages","operations"etc.) that can be directly returned from the handler.
Meanwhile, in formula fields it is instantiated automatically and its existence is
entirely transparent to the developer as the object's attributes and methods are
directly available as globals of the formula fields code.

## Pythonized Rossum objects

The TxScript environment provides instances of several pertinent Rossum objects.
These instances are directly available in globals namespace in formula fields, and
as atributes of theTxScriptinstance within serverless functions.

### Fields Object

Afieldobject is provided that allows access to the fields of
annotation content.

#### Attributes

Object attributes correspond to annotation fields, e.g.field.amount_totalwill evaluate
to the value of theamount_totalfield. The attributes behave specially:
- The field value types are pythonized. String fields arestrtype, number fields
arefloattype, date fields aredatetime.dateinstances.
- Since number fields are of typefloat, they should always be rounded when tested for
equality (because e.g. 0.1 + 0.2 isn't exactly 0.3 in floating-point arithmetics):round(field.amount_total, 2) == round(field.amount_total_base, 2)
The field value types are pythonized. String fields arestrtype, number fields
arefloattype, date fields aredatetime.dateinstances.
Since number fields are of typefloat, they should always be rounded when tested for
equality (because e.g. 0.1 + 0.2 isn't exactly 0.3 in floating-point arithmetics):round(field.amount_total, 2) == round(field.amount_total_base, 2)
> In other words, this expression referencing table columns will behave intuitively:
In other words, this expression referencing table columns will behave intuitively:

```
ifall(notis_empty(field.item_amount_base.all_values)):sum(default_to(field.item_amount_tax.all_values,0)*0.9+field.item_amount_base.all_values)
```

- You can access all in-multivalue field ids (table columns or simple multivalues)
via the.all_valuesproperty (e.g.field.item_amount.all_values). Its value
is a special sequence objectTableColumnthat behaves similarly to alist,
but with operators applying elementwise or distributive to scalars (NumPy-like).
Outside a single row context, the.all_valuesproperty is the only legal way
to work with these field ids. It is also a way to access a row of another multivalue 
from a multivalue formula.
> Example of iterating over rows in a formula field
Example of iterating over rows in a formula field

```
forrowinfield.line_items:ifnotis_empty(row.item_amount)androw.item_amount<0:show_warning("Negative amount",row.item_amount)
```

> Example of iterating over rows in serverless function hook
Example of iterating over rows in serverless function hook

```
fromtxscriptimportTxScript,is_emptydefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)forrowint.field.line_items:ifnotis_empty(row.item_amount)androw.item_amount<0:t.show_warning("Negative amount",row.item_amount)returnt.hook_response()
```

- You can access individual multivalue tuple rows by accessing the multivalue or tuple field id,
which provides a list offield-like objects that provide in-row tuple field members
as attributes named by their field id.
- Whilefield.amount_totalevaluates to a float-like value (or other types),
the value also provides anattrattribute that gives access to all
field schema, field object value and field object value content API object attributes
(i.e. one can writefield.amount_total.attr.rir_confidence).  Attributesposition,page,validation_sources,hiddenandoptionsare read-write.
- Fields that are not set (or are in an error state due to an invalid value)
evaluate to aNone-like value (except strings which evaluate to""),
but because of the above they are in fact not pure PythonNones. Therefore,
theymust notbe tested for usingis None. Instead, convenience helpersis_empty(field.amount_total)anddefault_to(field.amount_total, 0)should be used.
These helpers also behave correctly on string fields as well.
You can access individual multivalue tuple rows by accessing the multivalue or tuple field id,
which provides a list offield-like objects that provide in-row tuple field members
as attributes named by their field id.
Whilefield.amount_totalevaluates to a float-like value (or other types),
the value also provides anattrattribute that gives access to all
field schema, field object value and field object value content API object attributes
(i.e. one can writefield.amount_total.attr.rir_confidence).  Attributesposition,page,validation_sources,hiddenandoptionsare read-write.
Fields that are not set (or are in an error state due to an invalid value)
evaluate to aNone-like value (except strings which evaluate to""),
but because of the above they are in fact not pure PythonNones. Therefore,
theymust notbe tested for usingis None. Instead, convenience helpersis_empty(field.amount_total)anddefault_to(field.amount_total, 0)should be used.
These helpers also behave correctly on string fields as well.
> Example of updating field values in a serverless function hook
Example of updating field values in a serverless function hook

```
fromtxscriptimportTxScript,is_empty,default_todefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)ifnotis_empty(t.field.amount_tax_base):# Note: This type of operation is strongly discouraged in serverless# functions, since the modification is non-transparent to the user and# it is hard to trace down which hook modified the field.# Always prefer making amount_total a formula field!t.field.amount_total=t.field.amount_tax_base+default_to(t.field.amount_tax,0)# Merge po_number_external to the po_numbers multivalueifnotis_empty(t.field.po_number_external):t.field.po_numbers.all_values.remove(t.field.po_number_external)t.automation_blocker("External PO",t.field.po_numbers)else:t.field.po_number_external.attr.hidden=True# Filter out non-empty line items and add a discount line itemt.field.line_items=[rowforrowint.field.line_itemsifnotis_empty(row.item_amount)]if"10% discount"int.field.termsandnotis_empty(t.field.amount_total):t.field.line_items.append({"item_amount":-t.field.amount_total*0.1,"item_description":"10% discount"})t.field.line_items[-1].item_amount.attr.validation_sources.append("connector")t.field.line_items[-1].item_description.attr.validation_sources.append("connector")t.field.po_match.attr.options=[{"label":f"PO:{po}","value":po}forpoint.field.po_numbers.all_values]t.field.po_match.attr.options+=t.field.default_po_enum.attr.options# Update the currently selected enum option if the value fell out of the listif(len(t.field.po_match.attr.options)>0andt.field.po_matchnotin[po.valueforpoint.field.po_match.attr.options]):t.field.po_match=t.field.po_match.attr.options[0].valuereturnt.hook_response()
```

- You can assign values to the field attributes and modify the multivalue lists,
which will be reflected back in the app once your hook finishes.  (This is not
permitted in the read-only context of formula fields.)  You may construct
values of tuple rows as dicts indexed by column schema ids.
- You can modify thefield.*.attr.validation_sourceslist and it will be
reflected back in the app once your hook finishes.  It is not recommended
to perform any operation except.append("connector")(automates the field).
- Forenumtype fields, you can modify thefield.*.attr.optionslist
and it will be reflected back in the app once your hook finishes.  Elements of
the list are objects with thelabelandvalueattribute each.  You may
construct new elements as dicts with thelabelandvaluekeys.
- Outside of formula fields, you may access fields dynamically by computed schema
id (for example based on configuration variables) by using standard Python'sgetattr(field, schema_id).  Note that inside formula fields, such dynamic
access is not supported as it breaks automatic dependency tracking and formula
field value would not be recomputed once the referred field value changes.
- You may also access the parent of nested fields (within multivalues and/or
tuples) via their.parentattribute, or the enclosing multivalue field via.parent_multivalue.  This is useful when combined with thegetattrdynamic
field access.  For example, in the default Rossum schema naming setup,getattr(field, "item_quantity").parent_multivalue == field.line_items.
You can assign values to the field attributes and modify the multivalue lists,
which will be reflected back in the app once your hook finishes.  (This is not
permitted in the read-only context of formula fields.)  You may construct
values of tuple rows as dicts indexed by column schema ids.
You can modify thefield.*.attr.validation_sourceslist and it will be
reflected back in the app once your hook finishes.  It is not recommended
to perform any operation except.append("connector")(automates the field).
Forenumtype fields, you can modify thefield.*.attr.optionslist
and it will be reflected back in the app once your hook finishes.  Elements of
the list are objects with thelabelandvalueattribute each.  You may
construct new elements as dicts with thelabelandvaluekeys.
Outside of formula fields, you may access fields dynamically by computed schema
id (for example based on configuration variables) by using standard Python'sgetattr(field, schema_id).  Note that inside formula fields, such dynamic
access is not supported as it breaks automatic dependency tracking and formula
field value would not be recomputed once the referred field value changes.
You may also access the parent of nested fields (within multivalues and/or
tuples) via their.parentattribute, or the enclosing multivalue field via.parent_multivalue.  This is useful when combined with thegetattrdynamic
field access.  For example, in the default Rossum schema naming setup,getattr(field, "item_quantity").parent_multivalue == field.line_items.

### Annotation Object

Anannotationobject is provided, representing the pertinent annotation.

#### Attributes

The  available attributes are:id,url,statusprevious_status,automated,automatically_rejected,einvoice,metadata,created_at,modified_at,exported_at,confirmed_at,assigned_at,export_failed_at,deleted_at,rejected_at,purged_at
The timestamp attributes, such ascreated_at, are represented as a pythondatetimeinstance.
Theraw_dataattribute is a dict containing all attributes
of theannotationAPI object.
Theannotationalso has adocumentattribute. Thedocumentitself has the following attributes:id,url,arrived_at,created_at,original_file_name,metadata,mime-type, seedocumentfor more details.raw_datais also provided.
This enables txscript code such asannotation.document.original_file_name.
Theannotationalso has an optionalemailattribute. Theemailitself has the following attributes:id,url,created_at,last_thread_email_created_at,subject,email_from(identical tofromon API),to,cc,bcc,body_text_plain,body_text_html,metadata,annotation_counts,type,labels,filtered_out_document_count, seeemailfor more details.raw_datais also provided.
This enables txscript code such asannotation.email.subject.

#### Methods

> Example ofrejectingan annotation
Example ofrejectingan annotation

```
fromtxscriptimportTxScriptdefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)ifround(t.field.amount_total)!=round(t.field.amount_total_base+t.field.amount_tax):annotation.action("reject",note_content="Amounts do not match")ift.field.amount_total>100000:annotation.action("postpone")returnt.hook_response()
```

Theaction(verb: str, **args)method issues aPOSTon theannotationAPI object for a given verb in the formPOST /v1/annotations/{id}/{verb}, passing
additional arguments as specified.
(Notable verbs arereject,postponeanddelete.)
Note that Rossum authorization token passing must be enabled on the hook.

## TxScript Functions

Several functions are provided that map 1:1 to common extension hook return values.
These functions are directly available in globals namespace in formula fields, and
as methods of theTxScriptinstance within serverless functions.
> Example of raising a message in a formula field
Example of raising a message in a formula field

```
iffield.date_issue<date(2024,1,1):show_warning("Issue date long in the past",field.date_issue)
```

> Example of raising a message in serverless function hook
Example of raising a message in serverless function hook

```
fromtxscriptimportTxScriptdefrossum_hook_request_handler(payload:dict)->dict:t=TxScript.from_payload(payload)ift.field.date_issue<date(2024,1,1):t.show_warning("Issue date long in the past",field.date_issue)returnt.hook_response()
```

Theshow_error(),show_warning()andshow_info()functions raise a message,
either document-wide or attached to a particular field.  As arguments, they take
the message text (contentkey) and optionally the field to attach the message to
(converted to theidkey).  If no field is passed or if the field references 
a multivalue column, a document-level message is created.
For example, you may useshow_error()for fatals like a missing required field,
whereasshow_info()is suitable to decorate a supplier company id with its name
as looked up in the suppliers database.
> Example of a formula raising an automation blocker
Example of a formula raising an automation blocker

```
ifnotis_empty(field.amount_total)andfield.amount_total<0:automation_blocker("Total amount is negative",field.amount_total)
```

Theautomation_blocker()function analogously
raises an automation blocker, creatingautomation blockersoftypeextensionand therefore stopping theautomationwithout the need to create an error message.
The function signature is the same as for the show... methods above.

## Helper Functions and Aliases

Whenever a helper function is available, it should be used preferentially.
This is for the sake of better usability for admin users, but also because
these functions are e.g. designed to seamlessly work withTableColumninstances.
All identifiers below are directly available in globals namespace in formula fields.
Within serverless functions, they can be imported asfrom txscript import ...(or all of them obtained viafrom txscript import *).

### Helper Functions

Theis_empty(field.amount_total)boolean function returns True if the given
field has no value set. Use this instead of testing for None.
Thedefault_to(field.order_id, "INVALID")returns either the field value,
or a fallback value (string INVALID in this example) in case it is not set.

### Convenience Aliases

All string manipulations should be performed usingsubstitute(...),
which is an alias forre.sub.
These identifiers are automatically imported:
from datetime import date, timedelta

## Formula Fields

The Rossum Transaction Scripts can be evaluated in the context of
a formula-type field to automatically compute its value.
In this context, thefieldobject is read-only, i.e. side-effects on
values of other fields are prohibited (though you can still attach a message
or automation blocker to another field).
Theannotationobject is not available.
> This example sets the formula field value to either 0 or the output of the
specified regex substitution.
This example sets the formula field value to either 0 or the output of the
specified regex substitution.

```
iffield.order_id=="INVALID":show_warning("Falling back to zero",field.order_id)"0"else:substitute(r"[^0-9]",r"",field.order_id)
```

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
Field dependencies of formula fields are determined automatically.  The only caveat
is that in case you iterate over line item rows within the formula field code, you
must name your iteratorrow.

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
- Confidence automation: User only reviews documents with low data extraction
confidence ("tick" icon is not displayed for one or more fields) or
validation errors. By default, we automate documents that are duplicates and do not automate documents that edits (split) is proposed. You can change this inper-queue automation settings
- Full automation: All documents with no validation errors are exported or switched to confirmed state only if they do not contain a suggested edit (split). You can change this inper-queue automation settingsAn error triggered by a schema field constraint or connector validation
blocks auto-export even in full-automation level. In such case, non-required
fields with validation errors are cleared and validation is performed again.
In case the error persists, the document must be reviewed manually, otherwise
it is exported or switched to confirmed state.
No automation: User has to review all documents in the UI to validate
extracted data (default).
Confidence automation: User only reviews documents with low data extraction
confidence ("tick" icon is not displayed for one or more fields) or
validation errors. By default, we automate documents that are duplicates and do not automate documents that edits (split) is proposed. You can change this inper-queue automation settings
Full automation: All documents with no validation errors are exported or switched to confirmed state only if they do not contain a suggested edit (split). You can change this inper-queue automation settingsAn error triggered by a schema field constraint or connector validation
blocks auto-export even in full-automation level. In such case, non-required
fields with validation errors are cleared and validation is performed again.
In case the error persists, the document must be reviewed manually, otherwise
it is exported or switched to confirmed state.
Read more about theAutomation frameworkon our developer hub.

### Sources of field validation

Low-confidence fields are marked in the UI by an "eye" icon, we consider them
to be notvalidated. On the API level they have an emptyvalidation_sourceslist.
Validation of a field may be introduced by various sources: data extraction
confidence above a threshold, computation of various checksums (e.g. VAT rate,
net amount and gross amount) or a human review. These validations are recorded in
thevalidation_sourcelist. The data extraction confidence threshold may be
adjusted, seevalidation sourcesfor details.

### AI Confidence Scores

While there are multiple ways to automatically pre-validate fields, the most
prominent one is score-based validation based on AI Core Engine confidence
scores.
The confidence score predicted for each AI-extractd field is stored in therir_confidenceattribute. The score is a number between 0 and 1, and is
calibrated in such a way that it corresponds to the probability of a given
value to be correct. In other words, a field with score 0.80 is expected
to be correct 4 out of 5 times.
The value of thescore_threshold(can be set onqueue,
or individually perdatapointin schema; default is 0.8)
attribute represents the minimum score that triggers
automatic validation. Because of the score meaning, this directly corresponds
to the achieved accuracy. For example, if a score threshold for validation is
set at 0.8, that gives an expected error rate of 20% for that field.

## Autopilot

Autopilot is a automatic process removing "eye" icon from fields.
This process is based on past occurrence of field value on documents which has been
already processed in the same queue.
Read more about thisAutomation componenton our developer hub.

### Autopilot configuration

> Default Autopilot configuration
Default Autopilot configuration

```
{"autopilot":{"enabled":true,"search_history":{"rir_field_names":["sender_ic","sender_dic","account_num","iban","sender_name"],"matching_fields_threshold":2},"automate_fields":{"rir_field_names":["account_num","bank_num","iban","bic","sender_dic","sender_ic","recipient_dic","recipient_ic","const_sym"],"field_repeated_min":3}}}
```

Autopilot configuration can be modified inQueue.settingswhere you can set
rules for each queue.
If Autopilot is not explicitly disabled by switchenabledset tofalse, Autopilot is enabled.
Configuration is divided into two sections:

#### History search

This section configures process of finding documents from the same sender as the document which is currently being processed.
Annotation is considered from the same sender if it contains fields with samerir_field_nameand value as the current document.
> When at least two fields listed inrir_field_namesmatch values of the current document, document is is considered to have same sender
When at least two fields listed inrir_field_namesmatch values of the current document, document is is considered to have same sender

```
{"search_history":{"rir_field_names":["sender_ic","sender_dic","account_num"],"matching_fields_threshold":2}}
```


Attribute | Type | Description
--- | --- | ---
rir_field_names | list | List ofrir_field_namesused to find annotations from the same sender. This should contain fields which are unique for each sender. For examplesender_icorsender_dic.Please note that due to technical reasons it is not possible to usedocument_typein this field and it will be ignored.
matching_fields_threshold | int | At leastmatching_fields_thresholdfields must match current annotation in order to be considered from the same sender. See example on the right side.


#### Automate fields

This section describes rules which will be applied on annotations found in previous stepHistory search.
Field will have "eye" icon removed, if we have found at leastfield_repeated_minfields with samerir_field_nameand value
on documents found in stepHistory search.

Attribute | Type | Description
--- | --- | ---
rir_field_names | list | List ofrir_field_nameswhich can be validated based on past occurrence
field_repeated_min | int | Number of times field must be repeated in order to be validated

If any config section is missing, default value which you can see on the right side is applied.

# Using Triggers

Trigger REST operations can be foundhere
When an event occurs, all triggers of that type will perform actions of their related objects:

Related object | Action | Description
--- | --- | ---
Email template | Send email with the template to the event triggerer ifautomate=true | Automatically respond to document vendors based on the document's content. The document has to come from an email
Delete recommendations | Stop automation if one of the validation rules applies to the processed document | Based on the user's rules for delete recommendations, stop automation for the document which applies to these rules. The document requires manual evaluation


## Trigger Event Types

Trigger objects can have one of the following event types

Trigger Event type | Description (Trigger for an event of)
--- | ---
email_with_no_processable_attachments | An Email has been received without any processable attachments
annotation_created | Processing of the Annotation started (Rossum received the Annotation)
annotation_imported | Annotation data have been extracted by Rossum
annotation_confirmed | Annotation was checked and confirmed by user (or automated)
annotation_exported | Annotation was exported
validation | Document is being validated


### Trigger Events Occurrence Diagram

To show an overview of the Trigger events and when they are happening, this diagram was created.

## Trigger Condition

> Simple condition validating the presence ofvendor_idequal toMeat ltd.
Simple condition validating the presence ofvendor_idequal toMeat ltd.

```
{"$and":[{"field.vendor_id":{"$and":[{"$exists":true},{"$regex":"Meat ltd\\."}]}}]}
```

> Any required field is missing
Any required field is missing

```
{"$and":[{"required_field_missing":true}]}
```

> At least one of theiban,date_due, andsender_vat_idfields is missing
At least one of theiban,date_due, andsender_vat_idfields is missing

```
{"$and":[{"missing_fields":{"$elemMatch":{"$in":["iban","date_due","sender_vat_id"]}}}]}
```

> Will match if a required field is missing in the annotation, and the annotation contains avendor_idfield with a value that does matchMilk( inc\.)?regex. Or in other words, the trigger will activate if the Milk company sent us an invoice with missing data
Will match if a required field is missing in the annotation, and the annotation contains avendor_idfield with a value that does matchMilk( inc\.)?regex. Or in other words, the trigger will activate if the Milk company sent us an invoice with missing data

```
{"$and":[{"field.vendor_id":{"$and":[{"$exists":true},{"$regex":"Milk( inc\\.)?"}]}},{"required_field_missing":true}]}
```

> Will match if at least one of thedocument_type(Receipt,Other),language(CZ,EN,CH), orcurrency(USD,CZK) field match.
Will match if at least one of thedocument_type(Receipt,Other),language(CZ,EN,CH), orcurrency(USD,CZK) field match.

```
{"$or":[{"field.document_type":{"$in":["Receipt","Other"]},"field.language":{"$in":["CZ","EN","CH"]},"field.currency":{"$in":["CZK","USD"]}}]}
```

> Will match if filename is a subset of the specified regular expression.
Will match if filename is a subset of the specified regular expression.

```
{"$or":[{"filename":{"$regex":"Milk( inc\\.)?"}}]}
```

> Will match if filename is a subset of one of the specified regular expressions.
Will match if filename is a subset of one of the specified regular expressions.

```
{"$or":[{"filename":{"$or":[{"$regex":"Milk( inc\\.)?"},{"$regex":"Barn( inc\\.)?"}]}}]}
```

> Will match if a number of pages in the processed document is higher than the specified threshold.
Will match if a number of pages in the processed document is higher than the specified threshold.

```
{"$or":[{"number_of_pages":{"$gt":10}}]}
```

A subset of MongoDB Query Language. The annotation will get converted into JSON records behind the scenes. The trigger gets activated if at least one such record matches the condition according to theMQL query rules. Anullcondition matches any record, just like{}. Record format:

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

```
{
     "$and": [
       {"field.{schema_id}": {"$and": [{"$exists": true}, REGEX]}}
     ]
   }
```

Onlyannotation_importedtrigger event type:

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


Field | Required | Description
--- | --- | ---
field.{schema_id} |  | A field contained in the Annotation data. Theschema_idis theschemaid it got extracted under
required_field_missing |  | Any of theschema-required fields is missing. (*) Can not be combined withmissing_fields
missing_fields |  | At least one of theschemafields is missing. (*) Can not be combined withrequired_field_missing
field.{validation_field} |  | A field contained a list of Delete Recommendation data. Thevalidation_fieldis theschemaid it got extracted under
number_of_pages |  | A threshold value for the number of pages. A document with more pages is matched by the trigger.
filename |  | The filename or subset of filenames of the document is to match.
REGEX | true | Either{"$regex": re2}or{"$not": {"$regex": re2}}**. Usesre2 regex syntax

(*) A field is considered missing if any of the two following conditions is met
- the field hasui_configurationof typecapturedornulland no value was extracted for it andrir_cofidencescoreis at least 0.95
- the field hasui_configurationof other types (data,manual,formula, ...) and has an empty value
the field hasui_configurationof typecapturedornulland no value was extracted for it andrir_cofidencescoreis at least 0.95
the field hasui_configurationof other types (data,manual,formula, ...) and has an empty value
(**) The$notoption for REGEX is not valid for thevalidationtrigger.

## Triggering Email Templates

Email template REST operations can be foundhere.
To set up email template trigger automation, link an email template object to a trigger object and set itsautomateattribute totrue. Currently, only one trigger can be linked. To set up the recipient(s) of the automated emails,
you can usebuilt-in placeholdersor direct values in theto,cc, andbccfields in email templates.
Only some email template types and some trigger event types can be linked together:

Template type | Allowed trigger events
--- | ---
custom | *
email_with_no_processable_attachments | email_with_no_processable_attachments
rejection | annotation_imported
rejection_default | annotation_imported

Email templates of typerejectionandrejection_defaultwill also reject the associated annotation when triggered.
Every newly created queue hasdefault email templates. Some of them have a trigger linked,
including an email template of typeemail_with_no_processable_attachmentswhich can not have its trigger unlinked
or linked to another trigger. To disable its automation, set itsautomateattribute tofalse.

## Triggering Validation

Delete Recommendation REST operations can be foundhere.
To set up validation trigger automation, specify the rules for validation and set its enabled attribute totrue.
This trigger is only valid for thevalidationtrigger event.

## Hooks and Triggers Workflow

Sometimes it may happen that there is a need to know, what triggers and hooks and when are they run. That can be found in this workflow.

# Workflows

This feature must be explicitly enabled inqueue settings.

## Approval workflows

Approval workflows allow you to define multiple steps of approval process.
The workflow is started when the data extraction process is done (annotation isconfirmed) - it entersin_workflowstatus.
Then the annotation must beapprovedby defined approvers in order to be moved further (confirmedorexportedstatus).
The annotation is moved torejectedstatus if one of the assigneesrejectsit.
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

## Embedded mode workflow

The host application firstuploads a documentusing standard Rossum
API. During this process, anannotationobject
is created. It is possible to obtain astatusof the annotation object and wait for
the status to becometo_review(ready for checking) usingannotationendpoint.
As soon as importing of the annotation object has finished, an authenticated user
may callstart_embeddedendpoint to obtain a URL that is
to be included in iframe or popup browser window of the host application. Parameters of the call
arereturn_urlandcancel_urlthat are used to redirect to in a browser when user finishes
the annotation.
The URL contains security token that is used by embedded Rossum application to access Rossum API.
When the checking of the document has finished, user clicks
ondonebutton and host application is notified about finished annotation throughsaveendpoint of the connector HTTP API. By default, this call is made asynchronously, which
causes a lag (up to a few seconds) between the click ondonebutton and the call tosaveendpoint. However, it is possible to switch the calls to synchronous mode by switching theconnectorasynchronoustoggle tofalse(seeconnectorfor reference).

# API Reference

For introduction to the Rossum API, seeOverview
Most of the API endpoints require user to be authenticated, seeAuthenticationfor details.

## Annotation

> Example annotation object
Example annotation object

```
{"document":"https://<example>.rossum.app/api/v1/documents/314628","id":314528,"queue":"https://<example>.rossum.app/api/v1/queues/8199","schema":"https://<example>.rossum.app/api/v1/schemas/95","relations":[],"pages":["https://<example>.rossum.app/api/v1/pages/558598"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","rir_poll_id":"54f6b9ecfa751789f71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/314528","content":"https://<example>.rossum.app/api/v1/annotations/314528/content","time_spent":0,"metadata":{},"related_emails":[],"email":"https://<example>.rossum.app/api/v1/emails/96743","automation_blocker":null,"email_thread":"https://<example>.rossum.app/api/v1/email_threads/34567","has_email_thread_with_replies":true,"has_email_thread_with_new_replies":false,"organization":"https://<example>.rossum.app/api/v1/organizations/1","prediction":null,"assignees":[],"labels":[],"training_enabled":true,"einvoice":false}
```

An annotation object contains all extracted and verified data related to a
document. Every document belongs to a queue and is related to the schema
object, that defines datapoint types and overall shape of the extracted data.
Commonly you need to use queue theuploadendpoint to create annotations
instances.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the annotation | true
url | URL |  | URL of the annotation | true
status | enum |  | Status of the document, seeDocument Lifecyclefor list of value. | 
document | URL |  | Related document. | 
queue | URL |  | Queue that annotation belongs to. | 
schema | URL |  | Schema that defines content shape. | 
relations | list[URL] |  | (Deprecated) List of relations that annotation belongs to. | 
pages | list[URL] |  | List of rendered pages. | true
creator | URL |  | User that created the annotation. | true
created_at | datetime |  | Timestamp of object's creation. | true
modifier | URL |  | User that last modified the annotation. | 
modified_by | URL |  | User that last modified the annotation. | 
modified_at | datetime |  | Timestamp of last modification. | true
assigned_at | datetime |  | Timestamp of last assignment to a user or when the annotation was started being annotated. | true
confirmed_at | datetime |  | Timestamp when the annotation was moved to statusconfirmed. | true
deleted_at | datetime |  | Timestamp when the annotation was moved to statusdeleted. | true
exported_at | datetime |  | Timestamp of finished export. | true
export_failed_at | datetime |  | Timestamp of failed export. | true
purged_at | datetime |  | Timestamp when was annotation purged. | true
rejected_at | datetime |  | Timestamp when the annotation was moved to statusrejected. | true
confirmed_by | URL |  | User that confirmed the annotation. | true
deleted_by | URL |  | User that deleted the annotation. | true
exported_by | URL |  | User that exported the annotation. | true
purged_by | URL |  | User that purged the annotation. | true
rejected_by | URL |  | User that rejected the annotation. | true
rir_poll_id | string |  | Internal. | 
messages | list[object] | [] | List of messages from the connector (save). | 
content | URL |  | Link to annotation data (datapoint values), seeAnnotation data. | true
suggested_edit | URL |  | Link to Suggested edit object. | true
time_spent | float | 0 | Total time spent while validating the annotation. | 
metadata | object | {} | Client data. | 
automated | boolean | false | Whether annotation was automated | 
related_emails | list[URL] |  | List emails related with annotation. | true
email | URL |  | Related email that the annotation was imported by (for annotations imported by email). | true
automation_blocker | URL |  | Related automation blocker object. | true
email_thread | URL |  | Related email thread object. | true
has_email_thread_with_replies | bool |  | Related email thread contains more than oneincomingemail. | true
has_email_thread_with_new_replies | bool |  | Related email thread contains an unreadincomingemail. | true
organization | URL |  | Link to related organization. | true
automatically_rejected | bool |  | Read-only field of automatically_rejected annotation | true
prediction | object |  | Internal. | true
assignees | list[URL] |  | List of assigned users (only for internal purposes). | true
labels | list[URL] |  | List of selected labels | true
restricted_access | bool | false | Access to annotation is restricted | true
training_enabled | bool | true | Flag signalling whether the annotation should be used in the training of the instant learning component. | 
einvoice | bool | false | Flag signalling whether the annotation was ingested as an e-invoice. | true


```
"messages": [
    {
      "error": "Invalid invoice number format"
    }
  ]
```


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

> Start annotation of object319668
Start annotation of object319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/start'
```


```
{"annotation":"https://<example>.rossum.app/api/v1/annotations/319668","session_timeout":"01:00:00"}
```

POST /v1/annotations/{id}/start
Start reviewing annotation by the calling user. Can be called withstatusespayload to specify allowed statuses for starting annotation.
Returns409 Conflictif annotation fails to be in one of the specified states.

Attribute | Type | Default | Description | required
--- | --- | --- | --- | ---
statuses | list[str] | ["to_review", "reviewing", "postponed", "confirmed"] | List of allowed states for the starting annotation to be in | false


#### Response

Returns object withannotationandsession_timeoutkeys.

### Start embedded annotation

> Start embedded annotation of object319668
Start embedded annotation of object319668

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"return_url": "https://service.com/return", "cancel_url": "https://service.com/cancel"}'\'https://<example>.rossum.app/api/v1/annotations/319668/start_embedded'
```


```
{"url":"https://<example>.rossum.app/embedded/document/319668#authToken=1c50ae8552441a2cda3c360c1e8cb6f2d91b14a9"}
```

POST /v1/annotations/{id}/start_embedded
Start embedded annotation.

Key | Description | Required
--- | --- | ---
return_url | URL browser is redirected to in case of successful user validation | No
cancel_url | URL browser is redirected to in case of user canceling the annotation | No
postpone_url | URL browser is redirected to in case of user postponing the annotation | No
delete_url | URL browser is redirected to in case of user deleting the annotation | No
max_token_lifetime_s | Duration (in seconds) for which the token will be valid (default:queue'ssession_timeout, max: 162 hours) | No

Embedded annotation cannot be started by users with admin or organization group admin roles.
We strongly recommend starting embedded annotations by users withannotator_embeddeduser roleand permissions for the given queue only to limit the scope of actions that user is able to perform to required minimum.

#### Response

Returns object withurlthat specifies URL to be used in the browser
iframe/popup window. URL includes a token that is valid for this document only
for a limited period of time.

### Create embedded URL for annotation

> Create embedded URL for annotation object319668
Create embedded URL for annotation object319668

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"return_url": "https://service.com/return", "cancel_url": "https://service.com/cancel"}'\'https://<example>.rossum.app/api/v1/annotations/319668/create_embedded_url'
```


```
{"url":"https://<example>.rossum.app/embedded/document/319668#authToken=1c50ae8552441a2cda3c360c1e8cb6f2d91b14a9","status":"exported"}
```

POST /v1/annotations/{id}/create_embedded_url
Similar tostart embedded annotationendpoint but can be called for annotations with all statuses and does not switch status.

Key | Description | Required
--- | --- | ---
return_url | URL browser is redirected to in case of successful user validation | No
cancel_url | URL browser is redirected to in case of user canceling the annotation | No
postpone_url | URL browser is redirected to in case of user postponing the annotation | No
delete_url | URL browser is redirected to in case of user deleting the annotation | No
max_token_lifetime_s | Duration (in seconds) for which the token will be valid (default:queue'ssession_timeout, max: 162 hours) | No

Embedded annotation cannot be started by users with admin or organization group admin roles.
We strongly recommend creating embedded URLs by users withannotator_embeddeduser roleand permissions for the given queue only to limit the scope of actions that user is able to perform to required minimum.

#### Response


Key | Type | Description
--- | --- | ---
url | str | URL to be used in the browser iframe/popup window. URL includes a token that is valid for this document only for a limited period of time.
status | enum | Status of annotation, seeannotation lifecycle.


### Confirm annotation

> Confirm annotation of object319668
Confirm annotation of object319668

Key | Default | Description | Required
--- | --- | --- | ---
skip_workflows | False | Whether to skip workflows evaluation. Read more about workflowshere.bypass_workflows_allowedmust be set totrueinworkflows queue settingsin order to use this feature | No


```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/confirm'
```

POST /v1/annotations/{id}/confirm
Confirm annotation, switch status toexported(orexporting).
If theconfirmedstate is enabled, this call moves the annotation
to theconfirmedstatus.
Confirm annotation can optionally accept time spent data as described inannotation time spent, for internal use only.

#### Response


### Cancel annotation

> Cancel annotation of object319668
Cancel annotation of object319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/cancel'
```

POST /v1/annotations/{id}/cancel
Cancel annotation, switch its status back toto_revieworpostponed.
Cancel annotation can optionally accept time spent data as described inannotation time spent, for internal use only.

#### Response


### Approve annotation

> Approve annotation of object319668
Approve annotation of object319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{}'\'https://<example>.rossum.app/api/v1/annotations/319668/approve'
```

POST /v1/annotations/{id}/approve
Approve annotation, switch its status toexportingorconfirmed, or it stays inin_workflow, depending on the evaluation of the currentworkflow step
Only admin, organization group admin, or an assigned user with approver role can approve annotation in this state. Aworkflow activityrecord object will be created.

#### Response


Key | Type | Description
--- | --- | ---
status | string | New status of the annotation


### Assign annotation

> Assign annotation319668to the user1122
Assign annotation319668to the user1122

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/319668", \
  "assignees": ["https://<example>.rossum.app/api/v1/users/1122"], \
  "note_content": "I just want to reassign as I do not care about it"]}'\'https://<example>.rossum.app/api/v1/annotations/assing'
```

POST /v1/annotations/assign
Changeassigneesof the annotation.

Key | Type | Description | Required | Default
--- | --- | --- | --- | ---
annotations | list[URL] | List of annotations to change the assignees of (currenlty we support only one annotation at a time) | yes | 
assignees | list[URL] | List of users to be added as annotation assignees | yes | 
note_content | string | Content of the note that will be added to theworkflow activityof actionreassign(only applicable for annotation inin_workflowstate) | no | ""


#### Response


### Reject annotation

> Reject annotation of object319668
Reject annotation of object319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"note_content": "Rejected due to invalid due date."}'\'https://<example>.rossum.app/api/v1/annotations/319668/reject'
```

POST /v1/annotations/{id}/reject
Reject annotation, switch its status torejected.

Key | Description | Required | Default
--- | --- | --- | ---
note_content | Rejection note | No | ""
automatically_rejected | For internal use only (designates whether annotation is displayed as automatically rejected) in the statistics | No | false

Reject annotation can optionally accept time spent data as described inannotation time spent, for internal use only.
If rejecting inin_workflowstate, theannotation.workflow_run.workflow_statuswill also be set torejectedand aworkflow activityrecord object will be created. Only admin, organization group admin, or an assigned user can approve annotation in this state.

#### Response


Key | Type | Description
--- | --- | ---
status | string | New status of the annotation (rejected).
note | URL | Link to Note object.


### Switch to postponed

> Postpone annotation status of object319668topostponed
Postpone annotation status of object319668topostponed

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/postpone'
```

POST /v1/annotations/{id}/postpone
Switch annotation status topostpone.
Postpone annotation can optionally accept time spent data as described inannotation time spent, for internal use only.

#### Response


### Switch to deleted

> Switch annotation status of object319668todeleted
Switch annotation status of object319668todeleted

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/delete'
```

POST /v1/annotations/{id}/delete
Switch annotation status todeleted. Annotation with statusdeletedis still available in Rossum UI.
Delete annotation can optionally accept time spent data as described inannotation time spent, for internal use only.

#### Response


### Rotate the annotation

> Rotate the annotation319668
Rotate the annotation319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"rotation_deg": 270}'\'https://<example>.rossum.app/api/v1/annotations/319668/rotate"
```

POST /v1/annotations/{id}/rotate
Rotate a document. It requires one parameter:rotation_deg.
Status of the annotation is switched toimportingand the extraction phase begins over again.
After the new extraction, the value fromrotation_degfield is copied to pages rotation fieldrotation_deg.

Key | Description
--- | ---
rotation_deg | States degrees by which the document shall be rotated. Possible values: 0, 90, 180, 270.


#### Response


### Edit the annotation

> Edit the annotation319668
Edit the annotation319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/1", "rotation_deg": 90}, {"page": "https://<example>.rossum.app/api/v1/pages/2", "rotation_deg": 90}], "metadata": {"document": {"my_info": "something I want to store here"}, "annotation": {"some_key": "some value"}}}, {"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/2", "rotation_deg": 180}]}]}'\'https://<example>.rossum.app/api/v1/annotations/319668/edit"
```


```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/documents/320221"},{"document":"https://<example>.rossum.app/api/v1/documents/320552","annotation":"https://<example>.rossum.app/api/v1/documents/320222"}]}
```

POST /v1/annotations/{id}/editTo edit an annotation from webhook listening toannotation_status.initializeevent and action,
always usesplit endpointinstead.
Edit a document. It requires parameterdocumentsthat contains description of requested edits for annotations that should be
created from the original annotation. Description of each edit contains list of pages and rotation degree.
If used on an annotation in a way that after the editing only one document remains,
the original annotation will be edited. If multiple documents are to be created
after the call, status of the original annotation is switched tosplit,
status of the newly created annotations isimportingand the
extraction phase begins over again. To split the annotation into multiple
annotations, consider using the latest dedicatedsplit endpointinstead.

Key | Description
--- | ---
documents | Documents that should be created from the original annotation. Each document contains list of pages and rotation degree.

Thedocumentsobject consists of following available parameters:

Key | Type | Description
--- | --- | ---
pages | list[object] | A list of objects containing information aboutpage(URL) androtation_deg(integer)
metadata | object | (optional) A dictionary with attributesdocumentandannotationfor adding/updating metadata of edited annotation and its related document.


#### Response

Returnsresultswith a list of objects:

Key | Type | Description
--- | --- | ---
document | URL | URL to the document that was newly created after calling theeditendpoint.
annotation | URL | URL of the annotation assigned to the document.


### Split the annotation

> Split the annotation319668
Split the annotation319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/1", "rotation_deg": 90}, {"page": "https://<example>.rossum.app/api/v1/pages/2", "rotation_deg": 90}], "metadata": {"document": {"my_info": "something I want to store here"}, "annotation": {"some_key": "some value"}}}]}'\'https://<example>.rossum.app/api/v1/annotations/319668/split"
```


```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/documents/320221"}]}
```

POST /v1/annotations/{id}/split
Split a document based on editing rules. It requires parameterdocumentsthat contains description of requested edits for annotations that should be
created from the original annotation. Description of each edit contains list of pages and rotation degree.
When using this endpoint, status of the original annotation is switched tosplit,
status of the newly created annotations isimportingand the
extraction phase begins over again.
This endpoint can be used for splitting annotations also from webhook listening toannotation_content.initializeevent and action.

Key | Description
--- | ---
documents | Documents that should be created from the original annotation. Each document contains list of pages and rotation degree.

Thedocumentsobject consists of following available parameters:

Key | Type | Description
--- | --- | ---
pages | list[object] | A list of objects containing information aboutpage(URL) androtation_deg(integer)
metadata | object | (optional) A dictionary with attributesdocumentandannotationfor adding/updating metadata of edited annotation and its related document.

Edit annotation can optionally accept time spent data as described inannotation time spent, for internal use only.

#### Response

Returnsresultswith a list of objects:

Key | Type | Description
--- | --- | ---
document | URL | URL to the document that was newly created after calling theeditendpoint.
annotation | URL | URL of the annotation assigned to the document.


### Edit pages Start

> Start splitting the document and all its child documents.
Start splitting the document and all its child documents.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages/start'
```


```
{"parent_annotation":"http://<example>.rossum.app/api/v1/annotations/111","children":[{"url":"http://<example>.rossum.app/api/v1/annotations/120","queue":"http://<example>.rossum.app/api/v1/queues/1","status":"reviewing","started":true,"original_file_name":"large_4.pdf","parent_pages":[{"page":"http://<example>.rossum.app/api/v1/pages/142","rotation_deg":0},{"page":"http://<example>.rossum.app/api/v1/pages/143","rotation_deg":0,"deleted":true},{"page":"http://<example>.rossum.app/api/v1/pages/144","rotation_deg":0}],"values":{}},{"url":"http://<example>.rossum.app/api/v1/annotations/119","queue":"http://<example>.rossum.app/api/v1/queues/1","status":"reviewing","started":true,"original_file_name":"large_3.pdf","parent_pages":[{"page":"http://<example>.rossum.app/api/v1/pages/139","rotation_deg":0},{"page":"http://<example>.rossum.app/api/v1/pages/140","rotation_deg":0,"deleted":true},{"page":"http://<example>.rossum.app/api/v1/pages/141","rotation_deg":0}],"values":{}},{"url":null,"queue":"http://<example>.rossum.app/api/v1/queues/23","status":null,"started":false,"original_file_name":"deleted_section.pdf","parent_pages":[{"page":"http://<example>.rossum.app/api/v1/pages/145","rotation_deg":0,"deleted":true},{"page":"http://<example>.rossum.app/api/v1/pages/146","rotation_deg":90,"deleted":true}],"values":{"edit:language":"eng"}}],"session_timeout":"01:00:00"}
```

POST /v1/annotations/{id}/edit_pages/start
Starts editing the annotation and all its child documents (the documents into which the original document was split). The parent annotation must be in theto_review,splitorreviewingstate (for the calling user).
This call will "lock" the parent and child annotations from being edited. It returns some basic information about the parent annotation and a list of its children. Children to which the current user does not have rights contains only limited information.
If the parent annotation cannot be "locked", an error is returned. If the child annotation cannot be locked, it is skipped and sent in a response with valuestarted=False.

#### Response

Returns object with following keys.

Key | Type | Description
--- | --- | ---
parent_annotation | URL | URL of annotation
children | list[object] | List of child annotation objects
session_timeout | string | timeout in format "HH:MM:SS"

Thechildrenmember object has following keys:

Key | Type | Description
--- | --- | ---
url | URL | URL of the annotation
queue | URL | URL of the queue
status | string | Status of the parent annotation
started | boolean | was annotation started or not
original_file_name | string | File name of original document
parent_pages | list[object] | List of annotation pages from parent document with its rotation.
values | object | Edit valuesto be propagated to newly created annotations. Keys must be prefixed with "edit:", e.g. "edit:document_type".Schema Datapoint descriptiondescribes how it is used to initialize datapoint value.

Theparent_pagesmember object has following keys:

Key | Type | Description
--- | --- | ---
page | URL | URL of annotation
rotation_deg | integer | Rotation in degrees
deleted | boolean | Indicates whether the page is marked as deleted.

User doesn't have a right to edit parent annotation.

### Edit pages Cancel

> Cancel splitting the document and its child documents.
Cancel splitting the document and its child documents.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages/cancel'-d\'{"annotations": ["http://<example>.rossum.app/api/v1/annotations/119"], "cancel_parent": false, "processing_duration": {"time_spent": 10.0}}'
```

POST /v1/annotations/{id}/edit_pages/cancel
Cancel multiple started child annotations at once. By default cancel also parent annotation (optional).

Key | Type | Description
--- | --- | ---
annotations | list[URL] | List of urls of child annotations to cancel. Must be inreviewingstate.
cancel_parent | boolean | Cancel parent annotation. Optional, default true.
processing_duration | object | Optionalprocessing_durationobject


#### Response

Status:204on success.
Status:400when preconditions are not met.

### Edit pages

> Split the document and move one of the new child documents into different queue.
Split the document and move one of the new child documents into different queue.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"edit": [{"parent_pages": [{"page": "http://<example>.rossum.app/api/v1/pages/142", "rotation_deg": 90}], "values": {"edit:some_key": "some value"}},{"parent_pages": [{"page": "http://<example>.rossum.app/api/v1/pages/141", "rotation_deg": 90}], "target_queue": "https://<example>.rossum.app/api/v1/queues/23"}], "stop_parent": true}'
```


```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/annotations/320221"},{"document":"https://<example>.rossum.app/api/v1/documents/320552","annotation":"https://<example>.rossum.app/api/v1/annotations/320222"}]}
```

> Join of two child documents (784, 785, each with one page) into single new document.
Join of two child documents (784, 785, each with one page) into single new document.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"edit": [{"parent_pages": [{"page":"https://<example>.rossum.app/api/v1/pages/1088", "rotation_deg": 0}, {"page": "https://<example>.rossum.app/api/v1/pages/1089", "rotation_deg": 0}], "document_name": "joined_pages.pdf"}],"delete": ["https://<example>.rossum.app/api/v1/annotations/784", "https://<example>.rossum.app/api/v1/annotations/785"]}'
```


```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/annotations/786"}]}
```

> Move one child document into different queue.
Move one child document into different queue.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"move": [{"annotation": "https://<example>.rossum.app/api/v1/annotations/784", "target_queue": "https://<example>.rossum.app/api/v1/queues/23"}]}'
```


```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320551","annotation":"https://<example>.rossum.app/api/v1/annotations/784"}]}
```

> Delete one child document.
Delete one child document.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages'-d\'{"delete": ["https://<example>.rossum.app/api/v1/annotations/784"]}'
```


```
{"results":[]}
```

POST /v1/annotations/{parent_id}/edit_pages
Edit document pages, split and re-split already split document.
When using this endpoint, status of the original annotation (when not editing existing split) is switched tosplit,
status of the newly created annotations isimportingand the
extraction phase begins over again.
This endpoint can be used for splitting annotations also from webhook listening toannotation_content.initializeevent and action.

Key | Type | Description
--- | --- | ---
delete | list[URL] | Optional list of urls of child annotations to delete.
move | list[object] | Optional list of Move objects.
edit | list[object] | Optional list of Edit objects.
stop_reviewing | list[URL] | Optional list of urls of child annotations to stop reviewing. Must be inreviewingstate.
stop_parent | boolean | Stop also parent annotation. Optional, default true.
edit_data_source | String | Optional source of edit data. Eitherautomation,suggest,modified_suggestormanual.
processing_duration | object | Optionalprocessing_durationobject.

TheMove objecthas the following keys:

Key | Type | Description
--- | --- | ---
annotation | URL | URL of annotation.
target_queue | URL | URL of target queue.

TheEdit objecthas the following keys:

Key | Type | Description
--- | --- | ---
annotation | URL | Optional URL of annotation.
target_queue | URL | Optional URL of target queue.
document_name | String | Optional document name. When not provided, generated automatically.
parent_pages | list[object] | List of parent pages with rotation.
metadata | object | Metadata object. May contain objectsannotationandmetadatawhich are saved in created/edited annotation/document metadata.
values | object | Values to be propagated to newly created annotations. Keys must be prefixed with "edit:", e.g. "edit:document_type".

TheParent pageobject has the following keys:

Key | Type | Description | Required | Default value
--- | --- | --- | --- | ---
page | URL | URL of page. | yes | 
rotation_deg | int | Rotation angle in degrees with a step of 90 degrees | no | 0
deleted | boolean | Indicates whether the page is marked as deleted. | no | false


#### Response

Status:200on success.
Returnsresultswith a list of objects:

Key | Type | Description
--- | --- | ---
document | URL | URL to the document that was newly created after calling theeditendpoint.
annotation | URL | URL of the annotation assigned to the document.

Status:400when preconditions are not met.

### Edit pages in-place

> Edit pages of document and move to different queue.
Edit pages of document and move to different queue.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/111/edit_pages/in_place'-d\'{"parent_pages": [{"page": "http://<example>.rossum.app/api/v1/pages/142", "rotation_deg": 90}], "target_queue": "https://<example>.rossum.app/api/v1/queues/23"}'
```


```
{"results":[{"document":"https://<example>.rossum.app/api/v1/documents/2121","annotation":"https://<example>.rossum.app/api/v1/annotations/111"}]}
```

POST /v1/annotations/{parent_id}/edit_pages/in_place
Edit existing document pages without creating new annotations. You can rotate pages, delete pages or move the annotation into another queue.
This endpoint can be used for the embedded mode.

Key | Type | Description
--- | --- | ---
parent_pages | list[object] | List of parent pages with rotation.
target_queue | URL | Optional URL of target queue.
metadata | object | Optional metadata object. May contain objectsannotationandmetadatawhich are saved in created/edited annotation/document metadata.
edit_data_source | String | Optional source of edit data. Eitherautomation,suggest,modified_suggestormanual.
processing_duration | object | Optionalprocessing_durationobject.

TheParent pageobject has the following keys:

Key | Type | Description
--- | --- | ---
page | URL | URL of page.
rotation_deg | int | Rotation angle in deg. with step 90 deg.
deleted | boolean | Indicates whether the page is marked as deleted.


#### Response

Status:200on success.
Returnsresultswith a list of objects:

Key | Type | Description
--- | --- | ---
document | URL | URL to the document that was newly created after calling theeditendpoint.
annotation | URL | URL of the annotation assigned to the document.

Status:400when preconditions are not met.

### Search for text

> Search for text in annotation319668
Search for text in annotation319668

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319668/search?phrase=some'
```


```
{"results":[{"rectangle":[67.15157010915198,545.9286363906203,87.99106633081445,563.4617583852776],"page":1},{"rectangle":[45.27717884130982,1060.3084761056693,66.11667506297229,1077.8415981003266],"page":1}],"status":"ok"}
```

GET /v1/annotations/{id}/search
Search for a phrase in the document.

Argument | Type | Description
--- | --- | ---
phrase | string | A phrase to search for
tolerance | integer | AllowedEdit distancefrom the search phrase (number of removal, insertion or substitution operations that need to be performed for strings to match). Only used for OCR invoices (images, such as png or PDF with scanned images). Default value is computed aslength(phrase)/4.


#### Response

Returnsresultswith a list of objects:

Key | Type | Description
--- | --- | ---
rectangle | list[float] | Bounding box of an occurrence.
page | integer | Page of occurrence.


### Search for annotations

Supported ordering:id,arrived_at,assigned_at,assignees,automated,confirmed_at,confirmed_by__username,confirmed_by,created_at,creator__username,creator,deleted_at,deleted_by__username,deleted_by,document,exported_at,exported_by__username,exported_by,export_failed_at,has_email_thread_with_new_replies,has_email_thread_with_replies,labels,modified_at,modifier__username,modifier,original_file_name,purged_at,purged_by__username,purged_by,queue,rejected_at,rejected_by__username,rejected_by,relations__key,relations__parent,relations__type,rir_poll_id,status,workspace,email_thread,email_sender,field.<schema_id>.<format>(whereformatis one ofnumber,date,string).
> Obtain only annotations matching a complex filter
Obtain only annotations matching a complex filter

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'\-d'{"query": {"$and": [{"field.vendor_name.string": {"$eq": "ACME corp"}}, {"labels": {"$in": ["https://<example>.rossum.app/api/v1/labels/12", "https://<example>.rossum.app/api/v1/labels/34"]}}]}, "query_string": {"string": "explosives"}}'\'https://<example>.rossum.app/api/v1/annotations/search?ordering=status,confirmed_by__username,field.amount_total.number'
```


```
{"pagination":{"total":101,"total_pages":6,"next":"https://<example>.rossum.app/api/v1/annotations/search?search_after=eyJxdWVyeV9oYXNoIjogImM2ZWIzNjA5MDI1NWNmNTg4ODk0YWE5MGZiMjVmZjBlIiwgInNlYXJjaF9hZnRlciI6IFsxNTg2NTMwMzI0MDAwLCAyXSwgInJldmVyc2VkIjogZmFsc2V9%3A1NYBmgNCV-Ssmf7G9rd9vXnBY-BuvCZWrD95wcb2jIg","previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","document":"https://<example>.rossum.app/api/v1/documents/315877",...}]}
```

POST /v1/annotations/search
Search for annotations matching a complex filter

Key | Type | Description
--- | --- | ---
query | object | A subset of MongoDB Query Language (seequery definitionbelow)
query_string | object | Object with configuration for full-text search (seequery string definitionbelow)

Ifquery_stringis used together withquery, search is done as a conjunction of these expressions
(query_stringANDquery).
A list of definitions under a$andkey:

Key | Type | Description
--- | --- | ---
<meta_field> | object | Matches against annotation metadata according to <meta_field>. (Seedefinitionbelow)
field.<schema_id>.<type> | object | Matches against annotation content value according to <schema_id> treating it as <type>. (Seedefinitionbelow)

field.<schema_id>.typeis of type: string | number | date (in ISO 8601 format). Max. 256 characters long strings are allowed.
meta_fieldcan be one of:

Meta field name | Type
--- | ---
annotation | URL
arrived_at | date
assigned_at | date
assignees | URL
automated | bool
automatically_rejected | bool
confirmed_at | date
confirmed_by__username | string
confirmed_by | URL
created_at | date
creator__username | string
creator | URL
deleted_at | date
deleted_by__username | string
deleted_by | URL
document | URL
einvoice | bool
exported_at | date
exported_by__username | string
exported_by | URL
has_email_thread_with_new_replies | bool
has_email_thread_with_replies | bool
labels | URL
messages | string
modified_at | date
modifier__username | string
modifier | URL
original_file_name | string
purged_at | date
purged_by__username | string
purged_by | URL
queue | URL
rejected_at | date
rejected_by__username | string
rejected_by | URL
relations__key | string
relations__parent | URL
relations__type | string
restricted_access | bool
rir_poll_id | string
status | string
workspace | URL
email_thread | URL
email_sender | string


Key | Type | Description
--- | --- | ---
$startsWith | string | Matches the start of a value. Must be at least 2 characters long.
$anyTokenStartsWith | string | Matches the start of each token within a string. Must be at least 2 characters long.
$containsPrefixes | string | Same as $anyTokenStartsWith but query is split into tokens (words). Must be at least 2 characters long. Example queryquick brownmatchesquick brown foxbut alsobrown quick dogorquickiest brown fox, but notquick dog.
$emptyOrMissing | bool | Matches values that are empty or missing. Whenfalse, matches existing non-empty values.
$eq | $ne | number | string | date | URL | DefaultMQL behavior
$gt | $lt | $gte | $lte | number | string | date | DefaultMQL behavior
$in | $nin | list[number | string | URL] | DefaultMQL behavior

Related objects can besideloadedandquery fieldscan be used in the same way as whenlisting annotations.

#### Response

Returnspaginatedresponse with a list ofannotationobjects, likeannotations list
Value ofsearch_afteris not valid anymore. Retry the search with a different value.
> Obtain only annotations matching prefixexplosive
Obtain only annotations matching prefixexplosive

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'\-d'{"query_string": {"string": "expl"}}'\'https://<example>.rossum.app/api/v1/annotations/search?ordering=status,confirmed_by__username,field.amount_total.number'
```


```
{"pagination":{"total":101,"total_pages":6,"next":"https://<example>.rossum.app/api/v1/annotations/search?search_after=eyJxdWVyeV9oYXNoIjogImM2ZWIzNjA5MDI1NWNmNTg4ODk0YWE5MGZiMjVmZjBlIiwgInNlYXJjaF9hZnRlciI6IFsxNTg2NTMwMzI0MDAwLCAyXSwgInJldmVyc2VkIjogZmFsc2V9%3A1NYBmgNCV-Ssmf7G9rd9vXnBY-BuvCZWrD95wcb2jIg","previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","document":"https://<example>.rossum.app/api/v1/documents/315877",...}]}
```

Apply full-text search to datapoint values using a chosen term. The value is searched by
its prefix, separately for each term separated by whitespace, in case-insensitive way. Special characters
at the end of the strings are ignored. For example, when searching for a termLarge drink, all of the following
values passed would give a match:lar#,lar dri,dri.
We search also in the non-extracted page data, if the data are available.
Ifquery_stringis used together withquery, search is done as a conjunction of these expressions
(query_stringANDquery).

Key | Type | Description
--- | --- | ---
string | string | String to be used for full-text search. At least 2 characters need to be passed to apply this search. Max. 256 characters long strings are allowed.

Pagination is set by query parameters of the URL. Request body and ordering mustn't be changed when listing through pages, otherwise400response is returned.

Key | Default | Type | Description
--- | --- | --- | ---
page_size | 20 | int | Number of results per page. The maximum value is 500 (*)
search_after | null | string | Encoded value acting as a cursor (do not try to modify, only for internal purposes).

(*) For requests that sideloadcontent, the maximum value is limited to 100. Sideloading content for this endpoint is deprecated and
will be removed in the near future.

### Convert grid to table data

> Convert grid to tabular data in annotation319623
Convert grid to tabular data in annotation319623

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319623/content/37507202/transform_grid_to_datapoints'
```

POST /v1/annotations/{id}/content/{id of the child node}/transform_grid_to_datapoints
Transform grid structure to tabular data of related multivalue object.

#### Response

All tuple datapoints and their children are returned.

### Add new row to multivalue datapoint

> Add row to annotation319623multivalue37507202
Add row to annotation319623multivalue37507202

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/319623/content/37507202/add_empty'
```

POST /v1/annotations/{id}/content/{id of the child node}/add_empty
Adds a row to a multivalue table. This row will not be connected to the grid and modifications of the grid will not trigger any OCR on the cells of this row.

#### Response


### Validate annotation content

> Validate the content of annotation319623
Validate the content of annotation319623

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"updated_datapoint_ids": [37507204]}'\'https://<example>.rossum.app/api/v1/annotations/319623/content/validate'
```


```
{"messages":[{"id":"1038654","type":"error","content":"required","detail":{"hook_id":"42345","hook_name":"Webhook 8365","request_id":"6166deb3-2f89-4fc2-9359-56cc8e3838e4","is_exception":true,"timestamp":"2022-10-10T15:00:00.000000Z"}},{"id":"all","type":"error","content":"Whole document is invalid.","detail":{"hook_id":"94634","hook_name":"Function 4934","request_id":"5477aeb2-8f43-3fe1-9279-23bc8e4121e5","is_exception":true,"timestamp":"2022-10-10T15:00:00.000000Z"}},{"id":"1038456","type":"aggregation","content":"246.456","aggregation_type":"sum","schema_id":"vat_detail_tax2"}],"updated_datapoints":[{"id":37507205,"url":"https://<example>.rossum.app/api/v1/annotations/319623/content/37507205","content":{"value":"new value","page":1,"position":[0.0,1.0,2.0,3.0],"rir_text":null,"rir_page":null,"rir_position":null,"rir_confidence":null,"connector_position":[0.0,1.0,2.0,3.0],"connector_text":"new value"},"category":"datapoint","schema_id":"vat_rate","validation_sources":["connector","history"],"time_spent":0.0,"time_spent_overall":0.0,"options":[{"value":"value","label":"label"}],"hidden":false}],"suggested_operations":[{"op":"replace","id":"198143","value":{"content":{"value":"John","position":[103,110,121,122],"page":1},"hidden":false,"options":[],"validation_sources":["human"]}},{"op":"remove","id":"884061"}],"matched_trigger_rules":[{"type":"page_count","value":24,"threshold":10},{"type":"filename","value":"spam.pdf","regex":"^spam.*"},{"id":198143,"value":"foobar","type":"datapoint"}]}
```

POST /v1/annotations/{id}/content/validate
Validate the content of an annotation.
At first, the content is sent to thevalidate hookof connected extension.
Then some standard validations (datatype,constraintsare checked) are carried out in Rossum.
Additionally, if the annotation's respective queue has enabled delete recommendation conditions,
they are evaluated as well.

Key | Type | Description
--- | --- | ---
actions | list[enum] | Validation actions. Possible values :["user_update"],["user_update", "updated"]or["user_update", "started"](default:["user_update"])
updated_datapoint_ids | list[int] | List of IDs of datapoints that were changed since last call ofthis endpoint.


#### Response


Key | Type | Description
--- | --- | ---
messages | list[object] | Bounding box of an occurrence.
updated_datapoints | list[object] | Page of occurrence.
suggested_operations | list[object] | Datapoint operations suggested as a result of validation.
matched_trigger_rules | list[object] | Delete Recommendationrules that matched.

By default, messages for hidden datapoints are omitted. The behavior could be changed using themessages_for_hidden_datapoints=truequery parameter.
The message object contains attributes:

Key | Type | Description
--- | --- | ---
id | string | ID of the concerned datapoint;"all"for a document-wide issues
type | enum | One of:error,warning,infooraggregation.
content | string | A message shown in UI. Limited to 4096 characters.
detail | object | Detail object that gives more context to the message.
aggregation_type (*) | enum | Type of aggregation (currently supported"sum"aggregation type).
schema_id (*) | string | Identifier of schema datapoint for which is aggregation computed.

(*) Attribute present only in message with type"aggregation".
The message detail can contain the following attributes:

Key | Type | Description
--- | --- | ---
hook_id | int | ID of the hook,nullfor computed fields.
hook_name | string | Name of the hook.
request_id | string | ID of the request preceding this hook's response.
timestamp | string | Timestamp of the request preceding this hook's response.
is_exception | bool | Flag signaling non-200 response from the hook or error during computed field evaluation.
traceback_line_number | int | Line of the error in the computed field code.
source_id | int | Id of the datapoint which created this message.
source_schema_id | string | Schema id of the datapoint which created this message.

The updated datapoint object contains the subtrees ofdatapointsupdated from anextension.
The suggestions follow the same format as the one that can be specified in requests - please refer to theannotation dataAPI for a complete description.
The base of the response looks like this, the remaining fields depend on the "type" field and are
prone to change.

Key | Type | Description
--- | --- | ---
type | string | One of "page_count", "filename", "datapoint".


### List all annotations

> List all annotations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations'
```


```
{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/31336","pages":["https://<example>.rossum.app/api/v1/pages/561206"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","rir_poll_id":"54f6b9ecfa751789f71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},...},{...}]}
```

Retrieve all annotation objects.
Supported ordering:document,document__arrived_at,document__original_file_name,modifier,modifier__username,modified_by,modified_by__username,creator,creator__username,queue,status,created_at,assigned_at,confirmed_at,modified_at,exported_at,export_failed_at,purged_at,rejected_at,deleted_at,confirmed_by,deleted_by,exported_by,purged_by,rejected_by,confirmed_by__username,deleted_by__username,exported_by__username,purged_by__username,rejected_by__username

#### Filters

> Obtain only annotations with parent annotation 1500
Obtain only annotations with parent annotation 1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?relations__parent=1500'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/2","id":2,"queue":"https://<example>.rossum.app/api/v1/queues/1","schema":"https://<example>.rossum.app/api/v1/schemas/1","relations":["https://<example>.rossum.app/api/v1/relations/1"],..."url":"https://<example>.rossum.app/api/v1/annotations/2",...},{"document":"https://<example>.rossum.app/api/v1/documents/3","id":3,"queue":"https://<example>.rossum.app/api/v1/queues/2","schema":"https://<example>.rossum.app/api/v1/schemas/2","relations":["https://<example>.rossum.app/api/v1/relations/1"],..."url":"https://<example>.rossum.app/api/v1/annotations/3",...}]}
```

Filters may be specified to limit annotations to be listed.

Attribute | Description
--- | ---
status | Annotationstatus, multiple values may be separated using a comma
id | List of ids separated by a comma
modifier | User id
confirmed_by | User id
deleted_by | User id
exported_by | User id
purged_by | User id
rejected_by | User id
assignees | User id, multiple values may be separated using a comma
labels | Label id, multiple values may be separated using a comma
document | Document id
queue | List of queue ids separated by a comma
queue__workspace | List of workspace ids separated by a comma
relations__parent | ID of parent annotation defined in relatedRelationobject
relations__type | Type ofRelationthat annotation belongs to
relations__key | Key ofRelationthat annotation belongs to
arrived_at_before | ISO 8601 timestamp (e.g.arrived_at_before=2019-11-15)
arrived_at_after | ISO 8601 timestamp (e.g.arrived_at_after=2019-11-14)
assigned_at_before | ISO 8601 timestamp (e.g.assigned_at_before=2019-11-15)
assigned_at_after | ISO 8601 timestamp (e.g.assigned_at_after=2019-11-14)
confirmed_at_before | ISO 8601 timestamp (e.g.confirmed_at_before=2019-11-15)
confirmed_at_after | ISO 8601 timestamp (e.g.confirmed_at_after=2019-11-14)
modified_at_before | ISO 8601 timestamp (e.g.modified_at_before=2019-11-15)
modified_at_after | ISO 8601 timestamp (e.g.modified_at_after=2019-11-14)
deleted_at_before | ISO 8601 timestamp (e.g.deleted_at_before=2019-11-15)
deleted_at_after | ISO 8601 timestamp (e.g.deleted_at_after=2019-11-14)
exported_at_before | ISO 8601 timestamp (e.g.exported_at_before=2019-11-14 22:00:00)
exported_at_after | ISO 8601 timestamp (e.g.exported_at_after=2019-11-14 12:00:00)
export_failed_at_before | ISO 8601 timestamp (e.g.export_failed_at_before=2019-11-14 22:00:00)
export_failed_at_after | ISO 8601 timestamp (e.g.export_failed_at_after=2019-11-14 12:00:00)
purged_at_before | ISO 8601 timestamp (e.g.purged_at_before=2019-11-15)
purged_at_after | ISO 8601 timestamp (e.g.purged_at_after=2019-11-14)
rejected_at_before | ISO 8601 timestamp (e.g.rejected_at_before=2019-11-15)
rejected_at_after | ISO 8601 timestamp (e.g.rejected_at_after=2019-11-14)
restricted_access | Boolean
automated | Boolean
has_email_thread_with_replies | Boolean (related email thread contains more than oneincomingemails)
has_email_thread_with_new_replies | Boolean (related email thread contains unreadincomingemail)
search | String, seeAnnotation search

If this filter is used, annotations are filtered based on full-text search in annotation's datapoint values, original
file name, modifier user email and messages. Max. 256 characters allowed.

#### Query fields

> Obtain only subset of annotation attributes
Obtain only subset of annotation attributes

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?fields=id,url'
```


```
{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"id":320332,"url":"https://<example>.rossum.app/api/v1/annotations/320332"},{"id":319668,"url":"https://<example>.rossum.app/api/v1/annotations/319668"},...]}
```

In order to obtain only subset of annotation object attributes, one can use query parameterfields.

Argument | Description
--- | ---
fields | Comma-separated list of attributes to beincludedin the response.
fields! | Comma-separated list of attributes to beexcludedfrom the response.


#### Sideloading

> Sideload documents, modifiers and content
Sideload documents, modifiers and content

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?sideload=modifiers,documents,content&content.schema_id=item_amount_total'
```


```
{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320432","id":320332,...,"modifier":"https://<example>.rossum.app/api/v1/users/10775","status":"to_review","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/320332","content":"https://<example>.rossum.app/api/v1/annotations/320332/content","time_spent":0,"metadata":{}},...],"documents":[{"id":320432,"url":"https://<example>.rossum.app/api/v1/documents/320432",...},...],"modifiers":[{"id":10775,"url":"https://<example>.rossum.app/api/v1/users/10775",...},...],"content":[{"id":19434,"url":"https://<example>.rossum.app/api/v1/annotations/320332/content/19434","category":"datapoint","schema_id":"item_amount_total",...}...]}
```

> Sideload content filtered by schema_id
Sideload content filtered by schema_id

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations?sideload=content&content.schema_id=sender_id,vat_detail_tax'
```


```
{"pagination":{"total":22,"total_pages":1,"next":null,"previous":null},"results":[{"document":"https://<example>.rossum.app/api/v1/documents/320432","id":320332,...,"modifier":"https://<example>.rossum.app/api/v1/users/10775","status":"to_review","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/320332","content":"https://<example>.rossum.app/api/v1/annotations/320332/content","time_spent":0,"metadata":{}},...],"content":[{"id":15984,"url":"https://<example>.rossum.app/api/v1/annotations/320332/content/15984","category":"datapoint","schema_id":"sender_id",...},{"id":15985,"url":"https://<example>.rossum.app/api/v1/annotations/320332/content/15985","category":"datapoint","schema_id":"vat_detail_tax",...},...]}
```

In order to decrease the number of requests necessary for obtaining useful information about annotations, modifiers and documents can be sideloaded using query parametersideload. This parameter accepts comma-separated list of keywords:assignees,automation_blockers,confirmed_bys,content,creators,deleted_bys,documents,emails,exported_bys,labels,modifiers,notes,organizations,pages,purged_bys,queues,rejected_bys,related_emails,relations,child_relations,schemas,suggested_edits,workflow_runs,workspaces.
The response is then enriched by the requested keys, which contain lists of the sideloaded objects. Sideloadedcontentcan be filtered byschema_idto obtain only a subset of datapoints in content part of response, but is a deprecated feature and will be removed in the future.
Filter oncontentcan be specified using query parametercontent.schema_idthat accepts comma-separated list of requiredschema_ids.

#### Response

Returnspaginatedresponse with a list ofannotationobjects.

### Create an annotation

> Create an annotation

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"status": "created", "document": "https://<example>.rossum.app/api/v1/documents/315877", "queue": "https://<example>.rossum.app/api/v1/queues/8236", "content_data": [{category: "datapoint", schema_id: "doc_id", content: {value: "122"}, "validation_sources": []}], "values": {}, "metadata": {}}'\'https://<example>.rossum.app/api/v1/annotations'
```


```
{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/31336","pages":["https://<example>.rossum.app/api/v1/pages/561206"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"created","rir_poll_id":null,"messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null,...}
```

Create an annotation object.
Normally you create annotations via theuploadendpoint.
This endpoint could be used for creating annotation instances including their content and withstatusset to an
explicitly requested value. Currently onlycreatedis supported which is not touched by the rest of the platform
and is not visible via the Rossum UI. This allows for subsequent updates before switching the status toimportingso that it is passed through the rest of the upload pipeline.
The use-case for this is theupload.createdhook event where new
annotations could be created and the platform runtime then switches all such annotations' status toimporting.

Key | type | Description | Required
--- | --- | --- | ---
status | enum | Requested annotation status. Onlycreatedis currently supported. | Yes
document | URL | Annotation document. | Yes
queue | URL | Target queue. | Yes
content_data | list[object] | Array of annotation data content objects. | No
values | object | Values object as described inuploadendpoint. | No
metadata | object | Client data. | No
training_enabled | bool | Flag signalling whether the annotation should be used in the training of the instant learning component. Default istrue. | No


#### Response

Returnsannotationobject.

### Retrieve an annotation

> Get annotation object315777
Get annotation object315777

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777'
```


```
{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236","schema":"https://<example>.rossum.app/api/v1/schemas/31336","pages":["https://<example>.rossum.app/api/v1/pages/561206"],"creator":"https://<example>.rossum.app/api/v1/users/1","modifier":null,"modified_by":null,"assigned_at":null,"created_at":"2021-04-26T10:08:03.856648Z","confirmed_at":null,"deleted_at":null,"exported_at":null,"export_failed_at":null,"modified_at":null,"purged_at":null,"rejected_at":null,"confirmed_by":null,"deleted_by":null,"exported_by":null,"purged_by":null,"rejected_by":null,"status":"to_review","rir_poll_id":"54f6b9ecfa751789f71ddf12","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null,...}
```

GET /v1/annotations/{id}
Get an annotation object.

#### Response

Returnsannotationobject.

### Update an annotation

> Update annotation object315777
Update annotation object315777

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"document": "https://<example>.rossum.app/api/v1/documents/315877", "queue": "https://<example>.rossum.app/api/v1/queues/8236", "status": "postponed"}'\'https://<example>.rossum.app/api/v1/annotations/315777'
```


```
{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,"queue":"https://<example>.rossum.app/api/v1/queues/8236",..."status":"postponed","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null}
```

PUT /v1/annotations/{id}
Update annotation object.

#### Response

Returns updatedannotationobject.

### Update part of an annotation

> Update status of annotation object315777
Update status of annotation object315777

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"status": "deleted"}'\'https://<example>.rossum.app/api/v1/annotations/315777'
```


```
{"document":"https://<example>.rossum.app/api/v1/documents/315877","id":315777,..."status":"deleted","rir_poll_id":"a898b6bdc8964721b38e0160","messages":null,"url":"https://<example>.rossum.app/api/v1/annotations/315777","content":"https://<example>.rossum.app/api/v1/annotations/315777/content","time_spent":0,"metadata":{},"related_emails":[],"email":null}
```

PATCH /v1/annotations/{id}
Update part of annotation object.

#### Response

Returns updatedannotationobject.

### Copy annotation

> Copy annotation315777to a queue8236
Copy annotation315777to a queue8236

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"target_queue": "https://<example>.rossum.app/api/v1/queues/8236", "target_status": "to_review"}'\'https://<example>.rossum.app/api/v1/annotations/315777/copy'
```


```
{"annotation":"https://<example>.rossum.app/api/v1/annotations/320332"}
```

POST /v1/annotations/{id}/copy
Make a copy of annotation in another queue. All data and metadata are copied.

Key | Description
--- | ---
target_queue | URL of queue, where the copy should be placed.
target_status | Status of copied annotation (if not set, it stays the same)

If you want to directly reimport the copied annotation, you can usereimport=truequery parameter (such annotation will be billed).

#### Response

Returns URL of the new annotation object.

### Delete annotation

> Delete annotation315777
Delete annotation315777

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777'
```

DELETE /v1/annotations/{id}
Delete an annotation object from the database.
It also deletes the related page objects.
Never call this internal API, mark theannotation as deletedinstead.

#### Response


### Get suggested email recipients

> Get315777and78590annotations suggested email recipients
Get315777and78590annotations suggested email recipients

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/315777", https://<example>.rossum.app/api/v1/annotations/78590]'\'https://<example>.rossum.app/api/v1/annotations/suggested_recipients'
```


```
{"results":[{"source":"email_header","email":"don.joe@corp.us","name":"Don Joe"},...]}
```

POST /v1/annotations/suggested_recipients
Retrieves annotations suggested email recipients depending on Queuessuggested recipients settings.

#### Response

Returns a list ofsource objects.

#### Suggested recipients source object


Parameter | Description
--- | ---
source | Specifies where the email is found, seepossible sources
email | Email address of the suggested recipient
name | Name of the suggested recipient. Either a value from an email header or a value from parsing the email address


### Purge deleted annotations

> Purge deleted annotations from queue42
Purge deleted annotations from queue42

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/42"}'\'https://<example>.rossum.app/api/v1/annotations/purge_deleted'
```

POST /v1/annotations/purge_deleted
Start the asynchronous process of purging customer's data related to selected annotations withdeletedstatus. The following operations will happen:
- deleteannotation data
- deletepages
- remove content and file names ofdocuments
- remove annotations fromrelationsoftypeduplicate
- preserveannotationsobjects, move them topurgedstatus

Key | Type | Required | Description
--- | --- | --- | ---
annotations | list[URL] | false | List of annotations to be purged
queue | URL | false | Queue of which the annotations should be purged.

At least one ofannotations,queuefields must be filled in. The resulting set of annotations is the disjunction ofqueueandannotationsfilter.

#### Response

This is an asynchronous endpoint, status of annotations is changed topurgedand related objects are gradually being deleted.

### Annotation time spent

Time spent information can be optionally passed along the following annotation endpoints:cancel,confirm,delete,edit,postpone,reject.
> Confirm annotation315777and also update time spent data
Confirm annotation315777and also update time spent data

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"processing_duration": {"time_spent_active": 10.0, "time_spent_overall": 20.0, "time_spent_edit": 1.0, "time_spent_blockers": 2.0, "time_spent_emails": 3.0, "time_spent_opening": 1.5}}'\'https://<example>.rossum.app/api/v1/annotations/315777/confirm'
```

POST /v1/annotations/{id}/cancel
POST /v1/annotations/{id}/confirm
POST /v1/annotations/{id}/delete
POST /v1/annotations/{id}/edit
POST /v1/annotations/{id}/postpone
POST /v1/annotations/{id}/reject
Seeannotation processing durationobject.

### Get page spatial data

> Get spatial data for two first pages of annotation1421
Get spatial data for two first pages of annotation1421

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/1421/page_data?granularity=words&page_numbers=1,2'
```


```
{"results":[{"page_number":1,"granularity":"words","items":[{"position":[120,22,33,44],"text":"full"},{"position":[180,22,33,44],"text":"of"},{"position":[180,22,33,44],"text":"eels"},]},{"page_number":2,"granularity":"words","items":[{"position":[120,22,33,44],"text":"it"},{"position":[180,22,33,44],"text":"is"},{"position":[180,22,33,44],"text":"scratched"},]},]}
```

GET /v1/annotations/{id}/page_data
Get text content for every page, including position coordinates, considering granularity options like lines, words, characters, or complete page text content.

Key | Type | Default | Description | Required
--- | --- | --- | --- | ---
granularity | str |  | One oflines,words,chars,texts,barcodes. | Yes
page_numbers | str | First 20 pages of the document | Comma separated page numbers. Max. 20 page numbers, if there is more, they are silently ignored. | No


#### Response

Response result objects consist of following keys:

Key | Type | Description
--- | --- | ---
page_number | int | Number of page.
granularity | str | One oflines,words,chars,texts.
items | list[object] | List of objects divided by the chosen granularity.

Items consist of following keys:

Key | Type | Description
--- | --- | ---
position | list[int] | Coordinates of the item on the given page. In case oftextsgranularity, the result items objects are missingpositionkey, since thetextvalue is the full page text.
text | str | Value of the item.
type | str | Type of barcode. This value is present only for granularitybarcodes.

If there are no spatial data available for the given annotation.

### Translate page spatial data

> Get the translation for spatial data for page 2 of the annotation1421
Get the translation for spatial data for page 2 of the annotation1421

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"target_language": "en", "granularity": "lines", "page_numbers": [2]}'\'https://<example>.rossum.app/api/v1/annotations/1421/page_data/translate'
```


```
{"results":[{"page_number":2,"granularity":"lines","items":[{"position":[120,22,33,44],"text":"My hovercraft is"},{"position":[180,22,33,44],"text":"full of eels"},]},]}
```

POST /v1/annotations/{id}/page_data/translate
Get translation for all lines on a page, including position coordinates. Source language of the page is automatically detected. Translated text
of a page in a particular language is cached for 60 days.

Attribute | Type | Default | Description | Required
--- | --- | --- | --- | ---
granularity | str |  | Currently supported options:lines. | Yes
page_numbers | list[int] |  | Number of the page to be translated. Only one page at a time is currently supported. | Yes
target_language | str |  | Language* to translate the spatial data to. | Yes

*target_languagefield must be either in ISO 639-1 two-digit language code format or a combination of
ISO 639-1 two-digit language code followed by an underscore followed by an ISO 3166 2-digit country code. Supported languages
and their codes are as follows:

Key | Description
--- | ---
af | Afrikaans
sq | Albanian
am | Amharic
ar | Arabic
hy | Armenian
az | Azerbaijani
bn | Bengali
bs | Bosnian
bg | Bulgarian
ca | Catalan
zh | Chinese (Simplified)
zh-TW | Chinese (Traditional)
hr | Croatian
cs | Czech
da | Danish
fa-AF | Dari
nl | Dutch
en | English
et | Estonian
fa | Farsi (Persian)
tl | Filipino, Tagalog
fi | Finnish
fr | French
fr-CA | French (Canada)
ka | Georgian
de | German
el | Greek
gu | Gujarati
ht | Haitian Creole
ha | Hausa
he | Hebrew
hi | Hindi
hu | Hungarian
is | Icelandic
id | Indonesian
ga | Irish
it | Italian
ja | Japanese
kn | Kannada
kk | Kazakh
ko | Korean
lv | Latvian
lt | Lithuanian
mk | Macedonian
ms | Malay
ml | Malayalam
mt | Maltese
mr | Marathi
mn | Mongolian
no | Norwegian (Bokmål)
ps | Pashto
pl | Polish
pt | Portuguese (Brazil)
pt-PT | Portuguese (Portugal)
pa | Punjabi
ro | Romanian
ru | Russian
sr | Serbian
si | Sinhala
sk | Slovak
sl | Slovenian
so | Somali
es | Spanish
es-MX | Spanish (Mexico)
sw | Swahili
sv | Swedish
ta | Tamil
te | Telugu
th | Thai
tr | Turkish
uk | Ukrainian
ur | Urdu
uz | Uzbek
vi | Vietnamese
cy | Welsh


#### Response

Response result objects consist of following keys:

Key | Type | Description
--- | --- | ---
page_number | int | Number of page.
granularity | str | Currently supported options:lines.
items | list[object] | List of translated objects divided by the chosen granularity.

Items consist of following keys:

Key | Type | Description
--- | --- | ---
position | list[int] | Coordinates of the item on the given page.
text | str | Translated text.

If there are no spatial data available for the requested pages/annotation.

## Annotation Data

> Example annotation data
Example annotation data

```
{"content":[{"id":27801931,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801931","children":[{"id":27801932,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801932","content":{"value":"2183760194","normalized_value":"2183760194","page":1,"position":[761,48,925,84],"rir_text":"2183760194","rir_position":[761,48,925,84],"connector_text":null,"rir_confidence":0.99234},"category":"datapoint","schema_id":"document_id","validation_sources":["score"],"time_spent":0,"time_spent_overall":0,"hidden":false},{"id":27801933,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801933","content":{"value":"6/8/2018","normalized_value":"2018-08-06","page":1,"position":[283,300,375,324],"rir_text":"6/8/2018","rir_position":[283,300,375,324],"connector_text":null,"rir_confidence":0.98279},"category":"datapoint","schema_id":"date_issue","validation_sources":["score"],"time_spent":0,"time_spent_overall":0,"hidden":false},{"id":27801934,"url":"https://<example>.rossum.app/api/v1/annotations/319668/content/27801934","content":null,"category":"datapoint","schema_id":"email_button","validation_sources":["NA"],"time_spent":0,"time_spent_overall":0,"hidden":false},...}]}
```

Annotation data is used by the Rossum UI to display annotation data properly. Be
aware that values in attributevaluearenotnormalized (e.g. numbers, dates) and data structure
may be changed to accommodate UI requirements.
Top levelcontentcontains a list of section objects.resultsis currently
a copy ofcontentand is deprecated.

Attribute | Type | Description | Read-only
--- | --- | --- | ---
id | int64 | A unique ID of a given section. | true
url | URL | URL of the section. | true
schema_id | string | Reference mapping the object to the schema tree. | 
category | string | section | 
children | list | Array specifying objects that belong to the section. | 

Datapoint, multivalue and tuple objects:

Attribute | Type | Description | Read-only
--- | --- | --- | ---
id | int64 | A unique ID of a given object. | true
url | URL | URL of a given object. | true
schema_id | string | Reference mapping the object to the schema tree. | 
category | string | Type of the object (datapoint,multivalueortuple). | true
children | list | Array specifying child objects. Only available formultivalueandtuplecategories. | true
content | object | (optional) A dictionary of the attributes of a given datapoint (only available fordatapoint) seebelowfor details. | true
validation_sources | list[object] | Source of validation of the extracted data, see below. | 
time_spent | float | (optional) Time spent while actively working on a given node, in seconds. | 
time_spent_overall | float | (optional) Total time spent while validating a given node, in seconds. (only for internal purposes). | 
time_spent_grid | float | (optional) Total time spent while actively working on a grid, in seconds. Only available formultivaluecategory. (only for internal purposes). | 
time_spent_grid_overall | float | (optional) Total time spent while validating a given grid, in seconds. Only available formultivaluecategory. (only for internal purposes). | 
hidden | bool | If set to true, the datapoint is not visible in the user interface, but remains stored in the database. | 
no_recalculation | bool | If set to true, the datapoint's formula is not recalculated automatically. Only available fordatapointcategory editable formula datapoints. seebelow | 
grid | object | Specify grid structure, seebelowfor details. Only allowed for multivalue object. | 


#### Time spent

Time spents on datapoint are in seconds and are stored on datapoint object, for categorymultivalueordatapoint. For time spent on the annotation level, seeannotation processing duration.
Active time spent is stored intime_spent.
Overall time spent is stored intime_spent_overall.
Active time spent with an active magic grid is stored intime_spent_grid.
Overall time spent with an active magic grid is stored intime_spent_grid_overall.
Measuring starts when an annotation is not in a read-only mode after selecting a datapoint.
- another datapoint is selected. Selecting of datapoints when showing automation blockers doesn’t end or affect the measuring.
- the user leaves an annotation (for the same reasons as measuring ends on an annotation)
- the user goes to edit mode
When a measuring ends time_spent of the previously selected datapoint is incremented by measured time_spent and the result is patched together with adding a human validation source to validation sources.

#### Content object

Can be null for datapoints of typebutton

Attribute | Type | Description | Read-only
--- | --- | --- | ---
value | string | The extracted data of a given node. Maximum length: 1500 UTF characters. | 
normalized_value | string | Normalized value for date (in ISO 8601 format) and number fields (in JSON number format). | 
page | int | Number of page where the data is situated (see position). | 
position | list | List of the coordinates of the label box of the given node. (left, top, right, bottom) | 
rir_text | string | The extracted text, used as a reference for data extraction models. | true
rir_raw_text | string | Raw extracted text (only for internal purposes, may be removed in the future). | true
rir_page | int | The extracted page, used as a reference for data extraction models. | true
rir_position | list | The extracted position, used as a reference for data extraction models. (left, top, right, bottom) | true
rir_confidence | float | Confidence (estimated probability) that this field was extracted correctly. | true
connector_text | string | Text set by the connector. | true
connector_position | list | Position set by the connector. (left, top, right, bottom) | true
ocr_text | string | Value extracted by OCR, if applicable. (only for internal purposes, may be removed in the future) | true
ocr_raw_text | string | Raw value extracted by OCR, if applicable. (only for internal purposes, may be removed in the future) | true
ocr_position | string | OCR position, if applicable. (left, top, right, bottom) (only for internal purposes, may be removed in the future) | true

When bothvalueandnormalized_valueis set,normalized_valueis ignored on update.

#### Formula datapoints

Fordatapointcategory fields which have their schemaUI configuration'stypeproperty set toformulathe datapoint content and attributes are being updated automatically based on the provided formula code.
For editable formula fields (i.e. the correspondingUI configuration'seditproperty is not set
todisabledoption) the automatic recalculation can be disabled by setting the datapointno_recalculationflag to true.
To re-enable the formula automatic recalculation set theno_recalculationflag to false.

#### Validation sources

validation_sourcesproperty is a list of sources that verified the extracted data. When the list is
non-empty, datapoint is considered to be validated (and no eye-icon is displayed next to it in the Rossum UI).
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
> Example multivalue datapoint object with a grid
Example multivalue datapoint object with a grid

```
{"id":122852,"schema_id":"line_items","category":"multivalue","time_spent":3.4,"time_spent_overall":4.5,"time_spent_grid":1.2,"time_spent_grid_overall":2.3,"grid":{"parts":[{"page":1,"columns":[{"left_position":348,"schema_id":"item_description","header_texts":["Description"]},{"left_position":429,"schema_id":"item_quantity","header_texts":["Qty"]}],"rows":[{"top_position":618,"tuple_id":null,"type":"header"},{"top_position":649,"tuple_id":123,"type":"data"}],"width":876,"height":444}]},...}
```

Grid object (for internal use only) is used to store table vertical and horizontal separators and
related attributes. Every grid consists of zero or moreparts.
Everypartobject consists of several attributes:

Attribute | Type | Description
--- | --- | ---
page | int | A unique ID of a given object.
columns | list[object] | Description of grid columns.
rows | list[object] | Description of grid rows.
width | float | Total width of the grid.
height | float | Total height of the grid.

Every column contains attributes:

Attribute | Type | Description
--- | --- | ---
left_position | float | Position of the column left edge.
schema_id | string | Reference to datapoint schema id. Used ingrid-to-table conversion.
header_texts | list[string] | Extracted texts from column headers.

Every row contains attributes:

Attribute | Type | Description
--- | --- | ---
top_position | float | Position of the row top edge.
tuple_id | int | Id of the corresponding tuple datapoint if it exists else null.
type | string | Row type. Allowed values are specified in the schema, seegrid. Ifnull, the row is ignored duringgrid-to-table conversion.

Currently, it is only allowed to have one part per page (for a particular grid).

### Get the annotation data

> Get annotation data of annotation315777
Get annotation data of annotation315777

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/content'
```

GET /v1/annotations/{id}/content

#### Response

Returns annotation data.

### Update annotation data

> Update annotation data of annotation315777
Update annotation data of annotation315777

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": [{"category": "section", "schema_id": "invoice_details_section", "children": [{"category": "datapoint", "schema_id": "document_id", "content": {"value": "12345"}, "validation_sources": ["human"], "type": "string", "rir_confidence": 0.99}]}]}'\'https://<example>.rossum.app/api/v1/annotations/315777/content'
```


```
{"content":[{"category":"section","schema_id":"invoice_details_section","children":[{"category":"datapoint","schema_id":"document_id","content":{"value":"12345"},"type":"string","validation_sources":["human"]}]}]}
```

PATCH /v1/annotations/{id}/content
Update annotation data. The format is the same as for GET, datapoints missing in the uploaded content are preserved.

#### Response

Returns annotation data.

### Bulk update annotation data

> Example of body for bulk update of annotation data
Example of body for bulk update of annotation data

```
{"operations":[{"op":"replace","id":"198143","value":{"content":{"value":"John","position":[103,110,121,122],"page":1},"hidden":false,"options":[],"validation_sources":["human"]}},{"op":"remove","id":"884061"},{"op":"add","id":"884060","value":[{"schema_id":"item_description","content":{"page":1,"position":[162,852,371,875],"value":"Bottle"}}]}]}
```

POST /v1/annotations/{id}/content/operations
Allows to specify a sequence of operations that should be performed
on particular datapoint objects.
To replace adatapointvalue (or other supported attribute), usereplaceoperation:

Key | Type | Description
--- | --- | ---
op | string | Type of operation:replace
id | integer | Datapoint id
value | object | Updated data, format is the same as inAnotation Data. Onlyvalue(*),position,page,validation_sources,hiddenandoptionsattributes may be updated. Please note thatvalueis parsed and formatted.

(*)normalized_valuemay also be specified. When bothvalueandnormalized_valueare specified, they must match, otherwise datapoint won't be modified (this may be changed in the future).
Please note thatsection,multivalueandtupleshould not be updated.
To add a new row into a tablemultivalue, useaddoperation:

Key | Type | Description
--- | --- | ---
op | string | Type of operation:add
id | integer | Multivalue id (parent of new datapoint)
value | list[object] | Added row data. List of objects, format of the object is the same as inAnotation Data.schema_idattribute is required, onlyvalue,position,page,validation_sources,hiddenandoptionsattributes may be set.
validation_sources | list[object] | (optional) List of validation sources to set for all fields of the row by default (unless overriden invalue). This allows easily adding rows without breaking automation. See the "Validation sources" section below.

The row will be appended to the current list of rows.
For simple multivalues, the add operation can be used to add one child datapoint:

Key | Type | Description
--- | --- | ---
op | string | Type of operation:add
id | integer | Multivalue id (parent of new datapoint)
value | object | Updated data, format is the same as inAnotation Data. Onlyvalue(*),position,page,validation_sources,hiddenandoptionsattributes may be updated. Please note thatvalueis parsed and formatted.

To remove a row from a multivalue, useremoveoperation:

Key | Type | Description
--- | --- | ---
op | string | Type of operation:remove
id | integer | Datapoint id

Please note that onlymultivaluechildren datapoints may be removed.

#### Response

Returns annotation data.

### Replace annotation data by OCR

> Replace annotation data value by text extracted from a rectangle
Replace annotation data value by text extracted from a rectangle

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"rectangle": [316.2, 533.9, 352.7, 556.5], "page": "https://<example>.rossum.app/api/v1/pages/12221"}'\'https://<example>.rossum.app/api/v1/annotations/319668/content/21233223/select"
```

POST /v1/annotations/{id}/content/{id of child node}/select
Replace annotation data by OCR extracted from the rectangle of the document page. Payload of the request:

Key | Type | Description
--- | --- | ---
rectangle | list[float] | Bounding box of an occurrence.
page | URL | Page of occurrence.

When the rectangle size is unsuitable for OCR (any rectangle side is smaller
than 4 px), rectangle is extended to cover the text that overlaps with the
rectangle.

#### Response

Returns annotation data.

### Grid operations

> Update multiple grid parts and perform OCR on created and updated grids
Update multiple grid parts and perform OCR on created and updated grids

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"operations": [{"op": "update", "grid_index": 0, "grid": {"page": 1, "columns": [...], "rows": [...]}}]}'\'https://elis.rossum.ai/api/v1/annotations/319668/content/21233223/grid_operations"
```

POST /v1/annotations/{id}/content/{id of the multivalue}/grid_operations
This endpoint applies multiple operations on multiple grids for one multivalue and perform OCR if required, and update the multivalue with the resulting grid.
Forupdateoperation the position of the grid and its rows and columns can be changed, the column layout can be changed, but the row structure must be unchanged.
Payload of the request:

Key | Type | Description
--- | --- | ---
operations | list[object] | List of operations to apply to the grid


Key | Type | Description | Required
--- | --- | --- | ---
op | str | updateordeleteorcreate | Yes
grid_index | int | Index of the grid, | Yes
grid | object | New grid part | Forcreateandupdateoperations

The operations are applied sequentially. Thegrid_indexcorresponds to the index of the grid parts when the operation is applied. Combining different types of operations is not supported.

#### Response

Returns updated multivalue content as a tree, with only updated datapoints.

### Partial grid updates

> Update a grid part and perform OCR on modified cell datapoints
Update a grid part and perform OCR on modified cell datapoints

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"grid_index": 0, "grid": {"page": 1, "columns": [...], "rows": [...]}, "operations": {"columns": [{"op": "update", "schema_id": "vat_rate"}], "rows": [{"op": "delete", "tuple_id": 1256}]}'\'https://elis.rossum.ai/api/v1/annotations/319668/content/21233223/grid_parts_operations"
```

POST /v1/annotations/{id}/content/{id of the multivalue}/grid_parts_operations
Apply multiple operations on a grid and perform OCR on modified cell datapoints. Update the multivalue with the new grid.

Query parameter | Type | Default | Required | Description
--- | --- | --- | --- | ---
full_response | boolean | false | false | Use this parameter to get all datapoints in the grid part in the response

Payload of the request:

Key | Type | Description
--- | --- | ---
operations | object | Operations to apply to the grid
grid | object | Updated grid part
grid_index | int | Index of the grid part

Operations are grouped inrowsoperations andcolumnsoperations:

Key | Type | Description
--- | --- | ---
rows | list[object] | List of row operations
columns | list[object] | List of column operations

Single operations must contain the following parameters:

Key | Type | Description
--- | --- | ---
op | str | updateordeleteorcreate
row_index | int | Required for rowupdateand rowcreateoperations
tuple_id | int | Id of the tuple datapoint, required for rowdeleteand rowupdateoperations
schema_id | int | Id of the schema, required for column operations


axis | op | required parameters | OCR | Result
--- | --- | --- | --- | ---
columns | update | schema_id | Yes | Update column datapoints
columns | delete | schema_id | No | Set content to empty for column datapoints
rows | create | row_index | Yes | Insert a new row, create datapoints and perform OCR
rows | update | row_index, tuple_id | Yes | Update datapoints via OCR
rows | delete | tuple_id | No | Delete the tuple associated to this row

OCR is performed only for rows of extractable type as defined in the multivalue schema byrow_types_to_extract, or by default for rows of typedataonly.

#### Response

Returns updated multivalue content as a tree. By default, only updated datapoints and updated grid are returned. Add?full_response=trueto the url to get in the response all the datapoints in this grid.

### Send updated annotation data

> Send feedback on annotation315777Start the annotation
Send feedback on annotation315777

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/start'
```


```
{"annotation":"https://<example>.rossum.app/api/v1/annotations/315777","session_timeout":"01:00:00"}
```

> Get the annotation data
Get the annotation data

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/content'
```


```
{"id":37507206,"url":"https://<example>.rossum.app/api/v1/annotations/315777/content/37507206","content":{"value":"001","page":1,"position":[302,91,554,56],"rir_text":"000957537","rir_position":[302,91,554,56],"connector_text":null,"rir_confidence":null},"category":"datapoint","schema_id":"document_id","validation_sources":["human"],"time_spent":2.7,"time_spent_overall":6.1,"hidden":false}
```

> Patch the annotation

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Type:application/json'-d'{"content": {"value": "#INV00011", "position": [302, 91, 554, 56]}}'\'https://<example>.rossum.app/api/v1/annotations/315777/content/37507206'
```


```
{"id":37507206,"url":"https://<example>.rossum.app/api/v1/annotations/431694/content/39125535","content":{"value":"#INV00011","page":1,"position":[302,91,554,56],"rir_text":"","rir_position":null,"rir_confidence":null,"connector_text":null},"category":"datapoint","schema_id":"document_id","validation_sources":[],"time_spent":0,"time_spent_overall":0,"hidden":false}
```

> Confirm the annotation
Confirm the annotation

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/confirm'
```

PATCH /v1/annotations/{id}/content/{id of the child node}
Update a particular annotation content node.
It is enough to pass just the updated attributes in the PATCH payload.

#### Response

Returns updated annotation data for the given node.

## Annotation Processing Duration

> Example annotation processing duration
Example annotation processing duration

```
{"annotation":"https://<example>.rossum.app/api/v1/annotations/1","time_spent_active":12.3,"time_spent_overall":23.4,"time_spent_edit":1.23,"time_spent_blockers":2.34,"time_spent_emails":3.45,"time_spent_opening":4.56}
```

Annotation processing duration stores additional time spent information for an Annotation.
Annotation processing duration object:

Attribute | Type | Description | Read-only | Optional
--- | --- | --- | --- | ---
annotation | URL | Annotation that the processing duration is related to | true | 
time_spent_active | float | Total active time spent on the annotation, in seconds |  | true
time_spent_overall | float | Total time spent on the annotation, in seconds (same value as Annotation.time_spent) |  | true
time_spent_edit | float | Time spent editing the annotation, in seconds |  | true
time_spent_blockers | float | Time spent on annotation blockers, in seconds |  | true
time_spent_emails | float | Time spent on emails, in seconds |  | true
time_spent_opening | float | Time spent opening the annotation, in seconds |  | true

Measuring of time spent starts after an annotation is successfully started and datapoints and schema for annotation are fetched.
- user changes annotation status (confirm, postpone, delete, reject)
- user leaves validation (goes back to dashboard or another page)
- user goes to the next annotation
- user confirms changes in edit mode
- annotation time expires (checked periodically every 5 minutes if the current annotation is inreviewingstate)
- user closes a tab
time_spent_overallis the total time spent on the annotation,time_spent_activeis the same but measurement is stopped after 10 seconds of inactivity (no mouse movement nor key stroke or inactive tab).

### Get the annotation processing duration

> Get annotation processing duration of annotation315777
Get annotation processing duration of annotation315777

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/annotations/315777/processing_duration'
```

GET /v1/annotations/{id}/processing_duration
Get annotation processing duration.

#### Response

Returns annotation processing duration.

### Update annotation processing duration

> Update annotation processing duration of annotation315777
Update annotation processing duration of annotation315777

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"time_spent_active": 10.00, "time_spent_overall": 20.0, "time_spent_edit": 1.0, "time_spent_blockers": 2.0, "time_spent_emails": 3.0, "time_spent_opening": 1.5}'\'https://<example>.rossum.app/api/v1/annotations/315777/processing_duration'
```


```
{"annotation":"https://<example>.rossum.app/api/v1/annotations/315777","time_spent_active":10.0,"time_spent_overall":20.0,"time_spent_edit":1.0,"time_spent_blockers":2.0,"time_spent_emails":2.0,"time_spent_opening":1.5}
```

PATCH /v1/annotations/{id}/processing_duration
Update annotation processing duration.

#### Response

Returns annotation processing duration.

## Audit log

Audit log represents a log record of actions performed by users.
Only admin or organization group admins can access the log records.
Logs do not include records about changes made by Rossum representatives via internal systems. The log retention policy is set to 1 year.

Attribute | Type | Description
--- | --- | ---
organization_id | integer | ID of the organization.
timestamp* | str | Timestamp of the log record.
username | str | Username of the user that performed the action.
object_id | int | ID of the object on which the action was performed.
object_type | str | Type of the object on which the action was performed.
action | str | Type of the action performed.
content | object | Detailed content of the action.

*Timestamp is of the ISO 8601 format with UTC timezone e.g.2024-07-01T07:00:00.000000
contentconsists of the following elements:

Attribute | Type | Description
--- | --- | ---
path | str | Partial URL path of the request.
method | str | Method of the request.
request_id | str | ID of the request. Use this when contacting Rossum support with any related questions.
status_code | int | Status code of the response.
details | object | Details about the request (if available). For most cases, this field will be{}.

detailsmay include following attributes:

Attribute | Type | Description
--- | --- | ---
groups | list | Name of theuser rolesthat were sent (if sent) in a request on a user object.


### List all audit logs

> List all audit logs for update actions on user objects
List all audit logs for update actions on user objects

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/audit_logs?object_type=user&action=update'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"object_type":"user","action":"update","username":"john.doe@example.com","object_id":131,"timestamp":"2024-07-01T07:00:00.000000","details":{"path":"api/v1/users/131","method":"PATCH","request_id":"0aadfd75-8dcz-4e62-94d9-a23811d0d0b0","status_code":200,"payload":{"groups":["admin"]},}}]}
```

List audit log records for chosen objects and actions.
Using filters, you can narrow down the number of records.object_typeis a required filter.

Attribute | Type | Description | Required
--- | --- | --- | ---
object_type | str | Type of the object on which the action was performed. Available types aredocument,annotation,user. | Yes
action | str | Type of the action performed. See below. | No
object_id | int | ID of the object on which the action was performed. | No
timestamp_before | str | Filter for log entries before the given timestamp. | No
timestamp_after | str | Filter for log entries after the given timestamp. | No
username | str | Username of the user that performed the action. | No

Depending on theobject_type, you can choose to filter the logs based onaction. Eachobject_typesupports filtering by different actions:

object_type | Available actions
--- | ---
document | create
annotation | update-status
user | create, delete, purge, update, destroy, app_load*, reset-password, change_password

*app_loadvalue represents records of whenapi/v1/auth/userendpoint was called

#### Response

Returnspaginatedresponse with a list ofaudit logsobjects.

## Automation blocker

> Example automation blocker object
Example automation blocker object

```
{"id":1,"url":"https://<example>.rossum.app/api/v1/automation_blockers/1","annotation":"https://<example>.rossum.app/api/v1/annotations/4","content":[{"level":"datapoint","type":"low_score","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"score":0.901,"threshold":0.975}}]},{"level":"datapoint","type":"failed_checks","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234,"details":{"validation":"bad"}}},{"level":"datapoint","type":"no_validation_sources","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234}},{"level":"datapoint","type":"error_message","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"message_content":["Error 1","Error 2"]}}]},{"level":"annotation","type":"suggested_edit_present"},{"level":"annotation","type":"is_duplicate"},{"level":"annotation","type":"error_message","details":{"message_content":["Error 1"]}}]}
```

Automation blocker stores reason whyannotationwas notautomated.

Attribute | Type | Read-only | Description
--- | --- | --- | ---
id | integer | yes | AutomationBlocker object ID.
url | URL | yes | AutomationBlocker object URL.
annotation | URL | yes | URL of related Annotation object.
content | list[object] | no | List of reasons why automation is blocked.

Content consists of following elements

Attribute | Type | Description
--- | --- | ---
level | enum | Designates whether automation blocker relates to specificdatapointor to the wholeannotation.
type | enum | See below forpossible values.
schema_id | string | Only fordatapointlevel objects.
samples | list[object] | Contains sample of specific datapoints with detailed info (only fordatapointlevel objects). Only first 10 samples are listed.
samples_truncated | bool | Whether number samples were truncated to 10, or contains all of them.
details | object | Only forlevel:annotationwithtype:error_message. Containsmessage_contentwith list of error messages.


#### Automation blocker types

> low_scoreautomation blocker example
low_scoreautomation blocker example

```
{"level":"datapoint","type":"low_score","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"score":0.901,"threshold":0.975}},{"datapoint_id":1235,"details":{"score":0.968,"threshold":0.975}}]}
```

> failed_checksautomation blocker example
failed_checksautomation blocker example

```
{"level":"datapoint","type":"failed_checks","schema_id":"schema_id","samples_truncated":false,"samples":[{"datapoint_id":43,"details":{"validation":"bad"}}]}
```

> no_validation_sourcesautomation blocker example
no_validation_sourcesautomation blocker example

```
{"level":"datapoint","type":"no_validation_sources","schema_id":"schema_id","samples_truncated":false,"samples":[{"datapoint_id":412}]}
```

> error_messageautomation blocker example
error_messageautomation blocker example

```
[{"level":"annotation","type":"error_message","details":{"message_content":["annotation error"]}},{"level":"datapoint","type":"error_message","schema_id":"schema_id","samples_truncated":false,"samples":[{"datapoint_id":45,"details":{"message_content":["longer than 3 characters"]}}]}]
```

> delete_recommendationsautomation blocker example
delete_recommendationsautomation blocker example

```
[{"level":"annotation","type":"delete_recommendation_filename | delete_recommendation_page_count","details":{"message_content":["annotation error"]}},{"level":"datapoint","type":"delete_recommendation_field","schema_id":"document_type","samples_truncated":false,"samples":[{"datapoint_id":45}]}]
```

> extensionautomation blocker example
extensionautomation blocker example

```
[{"level":"annotation","type":"extension","details":{"content":["PO not found in the master data!"]}},{"level":"datapoint","type":"extension","schema_id":"sender_name","samples_truncated":false,"samples":[{"datapoint_id":1357,"details":{"content":["Unregistered vendor"]}}]}]
```

- automation_disabledautomation is disabled due toqueuesettingslevel: annotationonlyoccurs whenautomation levelis set toneverorautomation_enabledqueue settingsisfalse
- is_duplicateannotation is a duplicate of another one (there exists a relation ofduplicatetype)
andautomate_duplicatequeue settingsis set tofalselevel: annotationonly
- suggested_edit_presentthere is asuggested editby the AI engine andautomate_suggested_editqueue settingsis set tofalselevel: annotationonly
- low_scoreAI confidence scoreis lower thanscore_thresholdset for givendatapointlevel: datapointonly
- failed_checksschema field constraint or connector validation failedonly forlevel: datapoint
- no_validation_sourcesvalidation source list was reset e.g. by hook, so automation was blockedonly forlevel: datapoint
- error_messagefor bothlevels,annotationanddatapointerrortype messages received from connector
- Delete recommendationbased on validation trigger match for the documentdelete_recommendation_filename,delete_recommendation_page_countlevel: annotationonlydeletion was recommended based on filename/page count condition of the triggerdelete_recommendation_fieldonly forlevel: datapointdeletion recommended based on a value of given field (defined in the condition of trigger)
- extensionautomation blocker created by an extensionfor both levels -annotationanddatapoint
- automation is disabled due toqueuesettings
- level: annotationonly
- occurs whenautomation levelis set toneverorautomation_enabledqueue settingsisfalse
- annotation is a duplicate of another one (there exists a relation ofduplicatetype)
andautomate_duplicatequeue settingsis set tofalse
- level: annotationonly
- there is asuggested editby the AI engine andautomate_suggested_editqueue settingsis set tofalse
- level: annotationonly
- AI confidence scoreis lower thanscore_thresholdset for givendatapoint
- level: datapointonly
- schema field constraint or connector validation failed
- only forlevel: datapoint
- validation source list was reset e.g. by hook, so automation was blocked
- only forlevel: datapoint
- for bothlevels,annotationanddatapoint
- errortype messages received from connector
- delete_recommendation_filename,delete_recommendation_page_countlevel: annotationonlydeletion was recommended based on filename/page count condition of the trigger
- delete_recommendation_fieldonly forlevel: datapointdeletion recommended based on a value of given field (defined in the condition of trigger)
- level: annotationonly
- deletion was recommended based on filename/page count condition of the trigger
- only forlevel: datapoint
- deletion recommended based on a value of given field (defined in the condition of trigger)
- automation blocker created by an extension
- for both levels -annotationanddatapoint

### List all automation blockers

> List all automation blockers
List all automation blockers

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/automation_blockers'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/automation_blockers/1","annotation":"https://<example>.rossum.app/api/v1/annotations/4","content":[{"level":"datapoint","type":"low_score","schema_id":"invoice_id","samples_truncated":false,"samples":[{"datapoint_id":1234,"details":{"score":0.901,"threshold":0.975}}]},{"level":"datapoint","type":"failed_checks","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234,"details":{"validation":"bad"}}},{"level":"datapoint","type":"error_message","schema_id":"invoice_id","samples_truncated":false,"samples":{"datapoint_id":1234,"details":{"message_content":["Error 1","Error 2"]}}},{"level":"annotation","type":"suggested_edit_present"},{"level":"annotation","type":"is_duplicate"},{"level":"annotation","type":"error_message","details":{"message_content":["Error 1"]}}]}]}
```

GET /v1/automation_blockers
List all automation blocker objects.
Supported filters:annotation
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofautomation blockerobjects.

### Retrieve automation blocker

> Get automation blocker12
Get automation blocker12

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/automation_blockers/12'
```


```
{"id":12,"url":"https://<example>.rossum.app/api/v1/automation_blockers/12","annotation":"https://<example>.rossum.app/api/v1/annotations/481","content":[{"level":"annotation","type":"automation_disabled"}]}
```

GET /v1/automation_blockers/{id}

#### Response

Returnsautomation blockerobject.

## Connector

> Example connector object
Example connector object

```
{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":"strict=true","client_ssl_certificate":"-----BEGIN CERTIFICATE-----\n...","authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

A connector is an extension of Rossum that allows to validate and modify data
during validation and also export data to an external system. A connector
object is used to configure external or internal endpoint of such an extension
service. For more information seeExtensions.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the connector | true
name | string |  | Name of the connector (not visible in UI) | 
url | URL |  | URL of the connector | true
queues | list[URL] |  | List of queues that use connector object. | 
service_url | URL |  | URL of the connector endpoint | 
params | string |  | Query params appended to the service_url | 
client_ssl_certificate | string |  | Client SSL certificate used to authenticate requests. Must be PEM encoded. | 
client_ssl_key | string |  | Client SSL key (write only). Must be PEM encoded. Key may not be encrypted. | 
authorization_type | string | secret_key | String sent in HTTP headerAuthorizationcould be set tosecret_keyorBasic. For details seeConnector API. | 
authorization_token | string |  | Token sent to connector inAuthorizationheader to ensure connector was contacted by Rossum (displayed only toadminuser). | 
asynchronous | bool | true | Affects exporting: whentrue,confirmendpoint returns immediately and connector'ssaveendpoint is called asynchronously later on. | 
metadata | object | {} | Client data. | 
modified_by | URL | null | URL of the last connector modifier | true
modified_at | datetime | null | Date of last modification | true


### List all connectors

> List all connectors

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/connectors'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":"strict=true","client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
```

Retrieve all connector objects.
Supported filters:id,name,service_url
Supported ordering:id,name,service_url
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofconnectorobjects.

### Create a new connector

> Create new connector related to queue8199with endpoint URLhttps://myq.east-west-trading.com
Create new connector related to queue8199with endpoint URLhttps://myq.east-west-trading.com

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Connector", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "service_url": "https://myq.east-west-trading.com", "authorization_token":"wuNg0OenyaeK4eenOovi7aiF"}'\'https://<example>.rossum.app/api/v1/connectors'
```


```
{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

Create a new connector object.

#### Response

Returns createdconnectorobject.

### Retrieve a connector

> Get connector object1500
Get connector object1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/connectors/1500'
```


```
{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":null,"modified_at":null}
```

GET /v1/connectors/{id}
Get a connector object.

#### Response

Returnsconnectorobject.

### Update a connector

> Update connector object1500
Update connector object1500

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Connector (stg)", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "service_url": "https://myq.stg.east-west-trading.com", "authorization_token":"wuNg0OenyaeK4eenOovi7aiF"} \
  'https://<example>.rossum.app/api/v1/connectors/1500'
```


```
{"id":1500,"name":"MyQ Connector (stg)","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.stg.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

PUT /v1/connectors/{id}
Update connector object.

#### Response

Returns updatedconnectorobject.

### Update part of a connector

> Update connector URL of connector object1500
Update connector URL of connector object1500

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"service_url": "https://myq.stg2.east-west-trading.com"}'\'https://<example>.rossum.app/api/v1/connectors/1500'
```


```
{"id":1500,"name":"MyQ Connector","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"url":"https://<example>.rossum.app/api/v1/connectors/1500","service_url":"https://myq.stg2.east-west-trading.com","params":null,"client_ssl_certificate":null,"authorization_token":"wuNg0OenyaeK4eenOovi7aiF","asynchronous":true,"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

PATCH /v1/connectors/{id}
Update part of connector object.

#### Response

Returns updatedconnectorobject.

### Delete a connector

> Delete connector1500

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/connectors/1500'
```

DELETE /v1/connectors/{id}
Delete connector object.

#### Response


## Dedicated Engine

> Example engine object
Example engine object

```
{"id":3000,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","queues":[]}
```

A Dedicated Engine object holds specification and a current state of training setup for a Dedicated Engine.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the engine | true
name | string |  | Name of the engine | 
description | string |  | Description of the engine | 
url | URL |  | URL of the engine | true
status | enum | draft | Current status of the engine,see below | true
schema | url | null | Relateddedicated engine schema | 


#### Dedicated Engine Status

Can be one ofdraft,schema_review,annotating_initial,annotating_review,annotating_training,training_started,training_finished, andretraining
Ifstatusis notdraft, the whole engine and its schema become read-only.

### Request a new Dedicated Engine

> Request a new Dedicated Engine using a form (multipart/form-data)
Request a new Dedicated Engine using a form (multipart/form-data)

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fdocument_type="Custom invoice"-Fdocument_language="en-US"-Fvolume="9"\-Fsample_uploads=@document1.pdf-Fsample_uploads=@document2.pdf\'https://<example>.rossum.app/api/v1/dedicated_engines/request'
```


```
{"id":3001,"url":"https://<example>.rossum.app/api/v1/dedicated_engines/3001","name":"Requested engine - Custom invoice","status":"sample_review","description":"AI engine trained to recognize customer-provided data for the customer's specific data capture requirements","schema":null}
```

POST /v1/dedicated_engines/request
Request training of a new Dedicated Engine

Field | Type | Description | Required
--- | --- | --- | ---
document_type | str | Type of the document the engine should predict | True
document_language | str | Language of the documents | True
volume | int | Estimated volume per year | True
sample_uploads | list[FILE] | Multiple sample files of the documents. | 


#### Response

Returns createddedicated engineobject.

### List all dedicated engines

> List all dedicated engines
List all dedicated engines

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engines'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":3000,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}]}
```

GET /v1/dedicated_engines
Retrieve all dedicated engine objects.

#### Response

Returnspaginatedresponse with a list ofdedicated engineobjects.

### Create a new dedicated engine

> Create a new dedicated engine
Create a new dedicated engine

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Dedicated engine 1", "schema": "https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6001"}'\'https://<example>.rossum.app/api/v1/dedicated_engines'
```


```
{"id":3001,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3001","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6001"}
```

POST /v1/dedicated_engines
Create a new dedicated engine object.

#### Response

Returns createddedicated engineobject.

### Retrieve a dedicated engine

> Get dedicated engine object3000
Get dedicated engine object3000

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'
```


```
{"id":3000,"name":"Dedicated engine 1","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}
```

GET /v1/dedicated_engines/{id}
Get a dedicated engine object.

#### Response

Returnsdedicated engineobject.

### Update a dedicated engine

> Update dedicated engine object3000
Update dedicated engine object3000

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "New name", "schema": "https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'
```


```
{"id":3000,"name":"New name","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}
```

PUT /v1/dedicated_engines/{id}
Update dedicated engine object.

#### Response

Returns updateddedicated engineobject.

### Update part of a dedicated engine

> Update content URL of dedicated engine object3000
Update content URL of dedicated engine object3000

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "New name"}'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'
```


```
{"id":3000,"name":"New name","description":"AI engine trained to recognize data for the specific data capture requirement","url":"https://<example>.rossum.app/api/v1/dedicated_engines/3000","status":"draft","schema":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000"}
```

PATCH /v1/dedicated_engines/{id}
Update part of a dedicated engine object.

#### Response

Returns updateddedicated engineobject.

### Delete a dedicated engine

> Delete dedicated engine3000
Delete dedicated engine3000

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engines/3000'
```

DELETE /v1/dedicated_engines/{id}
Delete dedicated engine object.

#### Response


## Dedicated Engine Schema

> Example dedicated engine schema object
Example dedicated engine schema object

```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":["https://<example>.rossum.app/api/v1/queues/123","https://<example>.rossum.app/api/v1/queues/200","https://<example>.rossum.app/api/v1/queues/321"],"fields":[{"category":"datapoint","engine_output_id":"document_id","type":"string","label":"Document ID","description":"Document number","trained":true,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/123","schema_id":"document_id"},{"queue":"https://<example>.rossum.app/api/v1/queues/200","schema_id":"custom_name_document_id"}]},{"category":"multivalue","children":{"category":"datapoint","engine_output_id":"order_id","type":"string","label":"Order Number","description":"Purchase order identification (Order Numbers not captured as 'sender_order_id')","trained":false,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/200","schema_id":"custom_name_order_id"},{"queue":"https://<example>.rossum.app/api/v1/queues/321","schema_id":"order_id"}]}},{"category":"multivalue","engine_output_id":"line_items","type":"grid","label":"Line Items","description":"Line item column types.","trained":true,"children":{"category":"tuple","children":[{"category":"datapoint","engine_output_id":"table_column_tax","type":"number","label":"Item Tax","description":"Tax amount for the line","trained":true,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/123","schema_id":"table_column_tax"},{"queue":"https://<example>.rossum.app/api/v1/queues/200","schema_id":"custom_table_column_tax"}]},{"category":"datapoint","engine_output_id":"table_column_rate","type":"number","label":"Item Rate","description":"Tax rate for the line item","trained":true,"sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/321","schema_id":"table_column_rate"}]}]}}]}}
```

An engine schema is an object which describes what fields are available in the engine. Do not confuse engine schema withDocument Schema.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the engine schema | true
url | URL |  | URL of the engine schema | true
content | object |  | See below for description of the engine schema content | 

Schema can be edited only if its Dedicated Engine has statusdraft.

#### Content structure


Attribute | Type | Description
--- | --- | ---
training_queues | list[URL] | List of Queues that will be used for the training. Note that queues can't havedelete_afterfield set, otherwise a validation error is raised. (seequeue fields)
fields | list[object] | Container for fields declarations. It may contain only objects of categorymultivalueordatapoint


Attribute | Type | Description | Read-only
--- | --- | --- | ---
category | string | Category of the object,multivalue | 
engine_output_id | string | Unique name of the newextracted fieldin the trained Dedicated Engine | 
label | string | User-friendly label for an object, shown in the user interface | 
trained | bool | Whether the field was successfully trained | true
type | enum | Type of the trained field. One of:gridandfreeform. | 
description | string | Description of field attribute | 
children | object | Object specifying type of children. It may contain only objects with categoriestupleordatapoint. | 

Multivalue objects withdatapointchildren do not haveengine_output_id,label,trained,type, ordescriptionattributes

Attribute | Type | Description
--- | --- | ---
category | string | Category of the object,tuple
children | list[object] | Array specifying objects that belong to a given tuple. It may contain only objects with categorydatapoint.


Attribute | Type | Description | Read-only
--- | --- | --- | ---
category | string | Category of the object,datapoint | 
engine_output_id | string | Name of the newextracted fieldin the trained Dedicated Engine | 
label | string | User-friendly label for an object, shown in the user interface | 
trained | bool | Whether the field was successfully trained | true
type | enum | Type of the trained field. One of:number,string,date, andenum | 
description | string | Description of field attribute | 
sources | list[Sources] | Mapping describing the source Queues and their fields to train this field from | 


Attribute | Type | Description
--- | --- | ---
queue | URL | Queue to map the field from. Only one Queue per engine output is allowed
schema_id | string | Id of the field to map. The id must exist in the mapped Queue's schema


### Validate a dedicated engine schema

> Validate content and integrity of dedicated engine schema object
Validate content and integrity of dedicated engine schema object

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content":{"training_queues":["https://<example>.rossum.app/api/v1/queues/123"],"fields":[{"engine_output_id":"document_id","category":"datapoint","type":"string","label":"ID","description":"Document ID","sources":[{"queue":"https://<example>.rossum.app/api/v1/queues/123","schema_id":"document_id"}]}]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/validate'
```

POST /v1/dedicated_engine_schemas/validate
Validate dedicated engine schema object, check for errors. Additionally, to the basic checks done by the CRUD endpoints, this endpoint checks that:
- The declaredengine_output_ids are unique across the whole schema
- The mapped Queue datapoints (viaschema_ids) are of the same type as the declaredtype
- The mapped Queue datapoints ofenumtype have exactly the same option values declared
- Differentshapes of datapointsare not mixed together
- The mapped Queue datapoints of Multivalue-Tuple fields are of the samegrid/freeformtype
- When mapping to a single Multivalue-Tuple field, all the datapoints mapped from one Queue must come from a single tabular datapoint
- Multiple fields do not link to the same Queue Datapoint
- A mapped field either maps a Queue Datapoint withnull/emptyrir_field_namesor theengine_output_idmatches one of the mapped rir-namespacedrir_field_names(prefixed byrir:or nothing)

#### Response

Returns 200 and error description in case of validation failure.

### Predict a dedicated engine schema

> Predict a dedicated engine schema
Predict a dedicated engine schema

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"training_queues":["https://<example>.rossum.app/api/v1/queues/123", "https://<example>.rossum.app/api/v1/queues/200", "https://<example>.rossum.app/api/v1/queues/321"]}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/predict'
```


```
{"content":{"training_queues":["https://<example>.rossum.app/api/v1/queues/123","https://<example>.rossum.app/api/v1/queues/200","https://<example>.rossum.app/api/v1/queues/321"],"fields":[...]}}
```

POST /v1/dedicated_engine_schemas/predict
Try to predict a dedicated engine schema based on the provided training queue's schemas. The predicted schema is not guaranteed to pass/v1/dedicated_engine_schemas/validatecheck, only the checks done on engine schema save

#### Response

Returns 200 and predicted dedicated engine schema

### List all dedicated engine schemas

> List all dedicated engine schemas
List all dedicated engine schemas

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}]}
```

GET /v1/dedicated_engine_schemas
Retrieve all dedicated engine schema objects.

#### Response

Returnspaginatedresponse with a list ofdedicated engine schemaobjects.

### Create a new dedicated engine schema

> Create a new dedicated engine schema
Create a new dedicated engine schema

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": {"fields": [...], "training_queues": [...]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas'
```


```
{"id":6001,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6001","content":{"training_queues":[...],"fields":[...]}}
```

POST /v1/dedicated_engine_schemas
Create a new dedicated engine schema object.

#### Response

Returns createddedicated engine schemaobject.

### Retrieve a dedicated engine schema

> Retrieve dedicated engine schema object6000
Retrieve dedicated engine schema object6000

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'
```


```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
```

GET /v1/dedicated_engine_schemas/{id}
Get a dedicated engine schema object.

#### Response

Returnsdedicated engine schemaobject.

### Update a dedicated engine schema

> Update dedicated engine schema object6000
Update dedicated engine schema object6000

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": {"fields": [...], "training_queues": [...]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'
```


```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
```

PUT /v1/dedicated_engine_schemas/{id}
Update dedicated engine schema object.

#### Response

Returns updateddedicated engine schemaobject.

### Update part of a dedicated engine schema

> Update content URL of dedicated engine schema object6000
Update content URL of dedicated engine schema object6000

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": {"fields": [...], "training_queues": [...]}}'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'
```


```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
```

PATCH /v1/dedicated_engine_schemas/{id}
Update part of a dedicated engine schema object.

#### Response

Returns updateddedicated engine schemaobject.

### Delete a dedicated engine schema

> Delete dedicated engine schema6000
Delete dedicated engine schema6000

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/dedicated_engine_schemas/6000'
```

DELETE /v1/dedicated_engine_schemas/{id}
Delete a dedicated engine schema object.

#### Response


## Delete Recommendation

> Example delete-recommendation object
Example delete-recommendation object

```
{"id":1244,"enabled":true,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","triggers":["https://<example>.rossum.app/api/v1/triggers/500",]}
```


Attribute | Type | Required | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the delete recommendation. | true
enabled | boolean |  | Whether the associated triggers' rules should be active | 
url | URL |  | URL of the delete recommendation. | true
organization | URL |  | URL of the associated organization. | true
queue | URL |  | URL of the associated queue. | 
triggers | List[URL] |  | URL of the associated triggers. | 

A Delete-recommendation is an object that binds together triggers that fire when a document meets a queue's
criteria for a deletion recommendation. Currently, only binding to a single trigger is supported.
The trigger bound to a DeleteRecommendation must belong to the same queue.

### List all delete recommendations

> List all delete recommendations
List all delete recommendations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/delete_recommendations'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","triggers":["https://<example>.rossum.app/api/v1/triggers/500",],},...]}
```

GET /v1/delete_recommendations
Retrieve all delete recommendations objects.

#### Supported filters

Delete recommendations currently support the following filters:

Filter name | Type | Description
--- | --- | ---
queue | integer | Filter only delete recommendations associated with given queue id (or multiple ids).


#### Supported ordering

Delete recommendations currently support the following ordering:id,queue
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofdelete recommendationobjects.

### Retrieve a delete recommendation

> Get the delete recommendation object with ID1244
Get the delete recommendation object with ID1244

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'
```


```
{"id":1244,"enabled":true,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","triggers":["https://<example>.rossum.app/api/v1/triggers/500",]}
```

GET /v1/delete_recommendations/{id}
Get a delete recommendation object object.

#### Response

Returns adelete recommendationobject.

### Create a delete recommendation

> Create a new delete recommendation
Create a new delete recommendation

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/132", "triggers": ["https://<example>.rossum.app/api/v1/triggers/5000"], "queue": "https://<example>.rossum.app/api/v1/queues/4857", "enabled": "True"}'\'https://<example>.rossum.app/api/v1/delete_recommendations/'
```


```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","enabled":true,"triggers":["https://<example>.rossum.app/api/v1/triggers/5000"]}
```

POST /v1/delete_recommendations/
Create  a new delete recommendation

### Update a delete recommendation

> Update the delete recommendation object with ID1244
Update the delete recommendation object with ID1244

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"triggers": [], "enabled": "False"}'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'
```


```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","enabled":false,"triggers":[],...}
```

PUT /v1/delete_recommendations/{id}
Update a delete recommendation

### Update a part of a delete recommendation

> Update flag enabled of delete recommendation object1244
Update flag enabled of delete recommendation object1244

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"enabled": "False"}'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'
```


```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/delete_recommendations/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","enabled":false,...}
```

PATCH /v1/delete_recommendations/{id}
Update a part of a delete recommendation

### Remove a delete recommendation

> Remove the delete recommendation object 1244
Remove the delete recommendation object 1244

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/delete_recommendations/1244'
```

DELETE /v1/delete_recommendations/{id}
Remove a delete recommendation.

## Document

> Example document object
Example document object

```
{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628","s3_name":"272c2f01ae84a4e19a421cb432e490bb","parent":"https://<example>.rossum.app/api/v1/documents/203517","email":"https://<example>.rossum.app/api/v1/emails/987654","annotations":["https://<example>.rossum.app/api/v1/annotations/314528"],"mime_type":"application/pdf","creator":"https://<example>.rossum.app/api/v1/users/1","created_at":"2019-10-13T23:04:00.933658Z","arrived_at":"2019-10-13T23:04:00.933658Z","original_file_name":"test_invoice_1.pdf","content":"https://<example>.rossum.app/api/v1/documents/314628/content","attachment_status":null,"metadata":{}}
```

A document object contains information about one input file. To create it, one can:
- Useuploadendpoint
- import document by email
- create document via API
import document by email
create document via API

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the document | true
url | URL |  | URL of the document | true
s3_name | string |  | Internal | true
parent | URL | null | URL of the parent document (e.g. the zip file it was extracted from) | true
email | URL |  | URL of the email object that document was imported by (only for documents imported by email). | true
annotations | list[URL] |  | List of annotations related to the document. Usually there is only one annotation. | true
mime_type | string |  | MIME type of the document (e.g.application/pdf) | true
creator | URL |  | User that created the annotation. | true
created_at | datetime |  | Timestamp of document upload or incoming email attachment extraction. | true
arrived_at | datetime |  | (Deprecated) Seecreated_at | true
original_file_name | string |  | File name of the attachment or upload. | true
content | URL |  | Link to the document's raw content (e.g. PDF file). May benullif there is no file associated. | true
attachment_status | string | null | Reason, why the Document got filtered out on Email ingestion. Seeattachment status | true
metadata | object | {} | Client data. | 


#### Attachment status

Possible values:filtered_by_inbox_resolution,filtered_by_inbox_size,filtered_by_inbox_mime_type,filtered_by_inbox_file_name,filtered_by_hook_custom,filtered_by_queue_mime_type,hook_additional_file,filtered_by_insecure_mime_type,extracted_archive,failed_to_extract,processed,password_protected_archive,broken_imageandnull

### List all documents

> List all documents

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628",...},{"id":315609,"url":"https://<example>.rossum.app/api/v1/documents/315609",...}]}
```

Retrieve all document objects.
Supported filters:id,email,creator,arrived_at_before,arrived_at_after,created_at_before,created_at_after,original_file_name,attachment_status,parent
Supported ordering:id,arrived_at,created_at,original_file_name,mime_type,attachment_status
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofdocumentobjects.

### Retrieve a document

> Get document object314628
Get document object314628

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/314628'
```


```
{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628",...}
```

GET /v1/documents/{id}
Get a document object.

#### Response

Returnsdocumentobject.

### Create document

> Create new document using a form (multipart/form-data)
Create new document using a form (multipart/form-data)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/documents'
```

> Create new document by sending file in a request body
Create new document by sending file in a request body

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/documents'
```

> Create new document by sending file in a request body (UTF-8 filename must be URL encoded)
Create new document by sending file in a request body (UTF-8 filename must be URL encoded)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H"Content-Disposition: attachment; filename*=utf-8''document%20%F0%9F%8E%81.pdf"--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/documents'
```

> Create documents using basic authentication
Create documents using basic authentication

```
curl-u'east-west-trading-co@<example>.rossum.app:secret'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/documents'
```

> Create document with metadata and a parent document
Create document with metadata and a parent document

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\-Fmetadata='{"project":"Market ABC"}'\-Fparent='https://<example>.rossum.app/api/v1/documents/456700'\'https://<example>.rossum.app/api/v1/documents'
```


```
{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628",...}
```

Create a new document object.
Use this API call to create a document without an annotation. Suitable for creating documents
for mime types that cannot be extracted by Rossum. Only one document can be created per request.
The supported mime types are the same as fordocument import.
Allowed attributes for creation request:

Attribute | Type | Description
--- | --- | ---
content | bytes | The file to be uploaded.
metadata | object | Client data.
parent | URL | URL of the parent document (e.g. the original file based on which the uploaded content was created)


#### Response

Returns createddocumentobject.

### Update part of a document

> Update metadata of a document object314628
Update metadata of a document object314628

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"metadata": {"translation_file_name": "Rechnung.pdf"}}'\'https://<example>.rossum.app/api/v1/documents/314628'
```


```
{"id":314628,"url":"https://<example>.rossum.app/api/v1/documents/314628","metadata":{"translation_file_name":"Rechnung.pdf"},...}
```

PATCH /v1/documents/{id}
Update part of a document object.

### Document content

> Download document original
Download document original
To download multiple documents in one archive, refer todocuments downloadobject.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/314628/content'
```

GET /v1/documents/{id}/content
Get original document content (e.g. PDF file).

#### Response

Returns original document file.

### Permanent URL

> Download document original from a permanent URL
Download document original from a permanent URL

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/original/272c2f01ae84a4e19a421cb432e490bb'
```

GET /v1/original/272c2f01ae84a4e19a421cb432e490bb
Get original document content (e.g. PDF file).

#### Response

Returns original document file.

### Delete a document

> Delete document314628
Delete document314628

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/314628'
```

DELETE /v1/documents/{id}
Delete a document object from the database,
along with the related annotation and page objects,
but only if there are no datapoints associated to the annotation.
In order to reliably delete an annotation,mark it as deletedinstead.
This call also deletes the document data from Rossum systems.

#### Response

Document successfully deleted.
Document cannot be deleted due to existing datapoint references.

## Document Relation

> Example document relation object
Example document relation object

```
{"id":1,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124","https://<example>.rossum.app/api/v1/documents/125"],"url":"https://<example>.rossum.app/api/v1/document_relations/1"}
```

A document relation object introduces additional relations between annotations and documents. An annotation
can be related to one or more documents and it may belong to several such relations of different types at the
same time. These are additional to the main relation between the annotation and the document from which it was
created, seeannotation.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the document relation | true
type* | string | export | Type of relationship. Possible values areexport,einvoice. Seebelow | 
key* | string |  | Key used to distinguish several relationships of the same type. | 
annotation* | URL |  | Annotation | 
documents | list[URL] |  | List of related documents | 
url | URL |  | URL of the relation | true

* The combination oftype,keyandannotationattribute values must beunique.

#### Document relation types:

- export- Related documents are exports of the annotation data (e.g. in XML or JSON formats).
- einvoice- Related documents were created during import of an einvoice (e.g. validation report, visualisation, ...)

### List all document relations

> List all document relations
List all document relations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/document_relations'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/456","https://<example>.rossum.app/api/v1/documents/457"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}]}
```

GET /v1/document_relations
Retrieve all document relation objects.

Attribute | Description
--- | ---
id | ID of the document relation. Multiple values may be separated using a comma.
type | Relationtype. Multiple values may be separated using a comma.
annotation | ID of annotation. Multiple values may be separated using a comma.
key | Document relation key
documents | ID of related document. Multiple values may be separated using a comma.

Default ordering is byidin descending order. Supported other orderings are:id,type,annotation.
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofdocument relationobjects.

### Create a new document relation

> Create a new document relation of type export
Create a new document relation of type export

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "export", "annotation": "https://<example>.rossum.app/api/v1/annotations/123", "documents":'\'["https://<example>.rossum.app/api/v1/documents/124"]}'\'https://<example>.rossum.app/api/v1/document_relations'
```


```
{"id":789,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124"],"url":"https://<example>.rossum.app/api/v1/document_relations/789"}
```

POST /v1/document_relations
Create a new document relation object.

#### Response

Returns createddocument relationobject.

### Retrieve a document relation

> Get document relation object with id1500
Get document relation object with id1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/document_relations/1500'
```


```
{"id":1500,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124","https://<example>.rossum.app/api/v1/documents/125"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}
```

GET /v1/document_relations/{id}
Get a document relation object.

#### Response

Returnsdocument relationobject.

### Update a document relation

> Update the document relation object with id1500
Update the document relation object with id1500

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "export", "key": None, "annotation": "https://<example>.rossum.app/api/v1/annotations/123", "documents": ["https://<example>.rossum.app/api/v1/documents/124"]}'\'https://<example>.rossum.app/api/v1/document_relations/1500'
```


```
{"id":1500,"type":"edit","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}
```

PUT /v1/document_relations/{id}
Update document relation object.

#### Response

Returns updateddocument relationobject.

### Update part of a document relation

> Update related documents on document relation object with ID1500
Update related documents on document relation object with ID1500

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"documents": ["https://<example>.rossum.app/api/v1/documents/124", "https://<example>.rossum.app/api/v1/documents/125"]}'\'https://<example>.rossum.app/api/v1/document_relations/1500'
```


```
{"id":1500,"type":"export","key":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":["https://<example>.rossum.app/api/v1/documents/124","https://<example>.rossum.app/api/v1/documents/125"],"url":"https://<example>.rossum.app/api/v1/document_relations/1500"}
```

PATCH /v1/document_relations/{id}
Update part of a document relation object.

#### Response

Returns updateddocument_relationobject.

### Delete a document relation

> Delete empty document relation1500
Delete empty document relation1500

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/document_relations/1500'
```

DELETE /v1/document_relations/{id}
Delete a document relation object with empty related documents. If some documents still participate in the relation,
the caller must first delete those documents or update the document relation before deleting it.

#### Response


## Documents Download

> Example download object
Example download object

```
{"id":105,"url":"https://<example>.rossum.app/api/v1/documents/downloads/105","file_name":"test_invoice_1.pdf","expires_at":"2023-09-13T23:04:00.933658Z","content":"https://<example>.rossum.app/api/v1/documents/downloads/105/content",}
```

Set of endpoints enabling download of multipledocumentsat once. The workflow of such action is
as follows:
- create a download object via POST on /documents/downloads. The response of the call will contain ataskURL.
- call GET on the task URL. Watch the taskstatusto see when the task is ready.result_urlof a successful task will contain URL
to the download object.
- either call GET on the download object to get metadata about the object or call GET on the download object'scontentendpoint to
download the archive directly.
create a download object via POST on /documents/downloads. The response of the call will contain ataskURL.
call GET on the task URL. Watch the taskstatusto see when the task is ready.result_urlof a successful task will contain URL
to the download object.
either call GET on the download object to get metadata about the object or call GET on the download object'scontentendpoint to
download the archive directly.
A download object contains information about a downloadable archive in.zipformat.

Attribute | Type | Description | Read-only
--- | --- | --- | ---
id | integer | Id of the download object | true
url | URL | URL of the download object | true
expires_at | datetime | Timestamp of a guaranteed availability of the download object and its content. Set to the archive creation time plus 2 hours. Expired downloads are being deleted periodically. | true
file_name | string | Name of the archive to be downloaded. | true
content | URL | Link to the download's raw content. May benullif there is no archive associated yet. | true


### Retrieve a download

GET /v1/documents/downloads/{id}
Get a download object.

#### Response

Returnsdownloadobject.

### Create new download

> Create new download object
Create new download object

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"documents": ["https://<example>.rossum.app/api/v1/documents/123000", "https://<example>.rossum.app/api/v1/documents/123001"], "file_name": "monday_invoices.zip"}'\'https://<example>.rossum.app/api/v1/documents/downloads'
```


```
{"url":"https://<example>.rossum.app/api/v1/tasks/301"}
```

POST /v1/documents/downloads
Create a new download object.

Argument | Type | Required | Default | Description
--- | --- | --- | --- | ---
documents | list[URL] | true |  | Comma-separated list of document URLs to be included in the resulting downloadable archive. Max. 500 documents.
file_name | string |  | documents.zip | The filename of the resulting archive. Must include a.zipextension.
type | enum |  | document | One of:documentandsource_document.
zip | boolean |  | true | Useapplication/zipto bundle the download contents.

- Thezipvalue offalseis only applicable for single document downloads where thefile_nameif omitted in the
request is taken from the document being downloaded.
- Thesource_documentmeans that for each of the documents the most distant non-emptyparentdocument is put into the download.

#### Response

The responseLocationheader provides the task url (same as in the JSON body of the response).
Returns createdtaskobject.

### Retrieve download content

> Download archive with original documents files
Download archive with original documents files

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/documents/downloads/100/content'
```

GET /v1/documents/downloads/{id}/content
Get archive with originaldocumentfiles.

#### Response

Returns an archive with original document files.

## Email

> Example email object

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/emails/1234","queue":"https://<example>.rossum.app/api/v1/queues/4321","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","documents":["https://<example>.rossum.app/api/v1/documents/5678"],"parent":"https://<example>.rossum.app/api/v1/emails/1230","children":["https://<example>.rossum.app/api/v1/emails/1244"],"created_at":"2021-03-26T14:31:46.993427Z","last_thread_email_created_at":"2021-03-27T14:29:48.665478Z","subject":"Some email subject","from":{"email":"company@east-west.com","name":"Company East"},"to":[{"email":"east-west-trading-co-a34f3a@<example>.rossum.app","name":"East West Trading"}],"cc":[],"bcc":[],"body_text_plain":"Some body","body_text_html":"<div dir=\"ltr\">Some body</div>","metadata":{},"type":"outgoing","annotation_counts":{"annotations":3,"annotations_processed":1,"annotations_purged":0,"annotations_unprocessed":1,"annotations_rejected":1},"annotations":["https://<example>.rossum.app/api/v1/annotations/1","https://<example>.rossum.app/api/v1/annotations/2","https://<example>.rossum.app/api/v1/annotations/4"],"related_annotations":[],"related_documents":["https://<example>.rossum.app/api/v1/documents/3"],"filtered_out_document_count":2,"labels":["rejected"]}
```

An email object represents emails sent to Rossum inboxes.

Attribute | Type | Required | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the email | true
url | URL |  | URL of the email | true
queue | URL | true | URL of the associated queue | 
inbox | URL | true | URL of the associated inbox | 
parent | URL |  | URL of the parent email | 
email_thread | URL |  | URL of the associated email thread | true
children | list[URL] |  | List of URLs of the children emails | 
documents | list[URL] |  | List of documents attached to email | true
created_at | datetime |  | Timestamp of incoming email | true
last_thread_email_created_at | datetime |  | (Deprecated) Timestamp of the most recent email in this email thread | true
subject | string |  | Email subject | 
from | email_address_object |  | Information about sender containing keysemailandname. | true
to | list[email_address_object] |  | List that contains information about recipients. | true
cc | list[email_address_object] |  | List that contains information about recipients of carbon copy. | true
bcc | list[email_address_object] |  | List that contains information about recipients of blind carbon copy. | true
body_text_plain | string |  | Plain text email section (shortened to 4kB). | 
body_text_html | string |  | HTML email section (shortened to 4kB). | 
metadata | object |  | Client data. | 
type | string |  | Email type. Can beincomingoroutgoing. | true
annotation_counts | object |  | This attribute is intended forINTERNALuse only and may be changed in the future. Information about how many annotations were extracted from email attachments and in which state they currently are | true
annotations | list[URL] |  | List of URLs of annotations that arrived via email | true
related_annotations | list[URL] |  | List of URLs of annotations that are related to the email (e.g. rejected by that, added as attachment etc.) | true
related_documents | list[URL] |  | List of URLs of documents related to the email (e.g. by forwarding email containing document as attachment etc.) | true
creator | URL |  | User that have sent the email.Noneif email has been received via SMTP | true
filtered_out_document_count | integer |  | This attribute is intended forINTERNALuse only and may be changed in the future without notice. Number of documents automatically filtered out by Rossum smart inbox (this feature can be configured ininbox settings). | true
labels | list[string] |  | List of email labels. Possible values arerejection,automatic_rejection,rejected,automatic_status_changed_info,forwarded,reply | false
content | URL |  | URL of the emails content | true


#### Email address object


Attribute | Type | Default | Description | Required
--- | --- | --- | --- | ---
email | string |  | Email address | true
name | string |  | Name of the email recipient | 


#### Annotation counts object

This object stores numbers of annotations extracted from email attachments and their current status.

Attribute | Type | Description | Annotation status
--- | --- | --- | ---
annotations | integer | Total number of annotations | Any
annotations_processed | integer | Number of processed annotations | exported,deleted,purged,split
annotations_purged | integer | Number of purged annotations | purged
annotations_unprocessed | integer | Number of not yet processed annotations | importing,failed_import,to_review,reviewing,confirmed,exporting,postponed,failed_export
annotations_rejected | integer | Number of rejected annotations | rejected
related_annotations | integer | Total number of related annotations | Any


#### Email labels

Email objects can have assigned any number of labels.

Label name | Description
--- | ---
rejection | Outgoing informative email sent by Rossum after email was manually rejected.
automatic_rejection | Informative automatic email sent by Rossum when no document was extracted from incoming email.
automatic_status_changed_info | Informative automatic email sent by Rossum about document status change.
rejected | Incoming email rejected together with all attached documents.
forwarded | Outgoing email sent by forwarding other email.
reply | Outgoing email sent by replying to another email.


### List all emails

> List all emails

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/emails'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1234,"url":"https://<example>.rossum.app/api/v1/emails/1234","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","queue":"https://<example>.rossum.app/api/v1/queues/4321","documents":["https://<example>.rossum.app/api/v1/documents/5678"],...]}
```

Retrieve all emails objects.
Supported filters:id,created_at_before,created_at_after,subject,queue,inbox,documents,from__email,from__name,to,last_thread_email_created_at_before,last_thread_email_created_at_after,type,email_thread,has_documents
Supported ordering:id,created_at,subject,queue,inbox,from__email,from__name,last_thread_email_created_at
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofemailobjects.

### Retrieve an email

> Get email object1244

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/emails/1244'
```


```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/emails/1244","queue":"https://<example>.rossum.app/api/v1/queues/4321","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","documents":["https://<example>.rossum.app/api/v1/documents/5678"],"parent":"https://<example>.rossum.app/api/v1/emails/1230","children":[],"arrived_at":"2021-03-26T14:31:46.993427Z","last_thread_email_created_at":"2021-03-27T14:29:48.665478Z","subject":"Some email subject","from":{"email":"company@east-west.com"},"to":[{"email":"east-west-trading-co-a34f3a@<example>.rossum.app"}],"cc":[],"bcc":[],"body_text_plain":"","body_text_html":"","metadata":{},"type":"outgoing","labels":[],...}
```


#### Response


### Update an email

> Update email object1244
Update email object1244

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "inbox": "https://<example>.rossum.app/api/v1/inboxes/8236", "subject": "Some subject", "to": [{"email": "jack@east-west-trading.com"}]}'\'https://<example>.rossum.app/api/v1/emails/1244'
```


```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/emails/1244","queue":"https://<example>.rossum.app/api/v1/queues/4321","inbox":"https://<example>.rossum.app/api/v1/inboxes/8199","documents":[],"parent":null,"children":[],"arrived_at":"2021-03-26T14:31:46.993427Z","last_thread_email_created_at":"2021-03-27T14:29:48.665478Z","subject":"Some subject","from":null,"to":[{"email":"jack@east-west-trading.com"}],"body_text_plain":"","body_text_html":"","metadata":{},"type":"outgoing","labels":[],...}
```


#### Response

Returns updatedemailobject.

### Update part of an email

> Update subject of email object1244
Update subject of email object1244

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"subject": "Some subject"}'\'https://<example>.rossum.app/api/v1/emails/1244'
```


```
{"id":1244,"subject":"Some subject",...}
```

PATCH /v1/emails/{id}
Update part of email object.

#### Response

Returns updatedemailobject.

### Import email

> Import email using a form (multipart/form-data)
Import email using a form (multipart/form-data)

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fraw_message=@email.eml-Frecipient="east-west-trading-co-a34f3a@<example>.rossum.app"\'https://<example>.rossum.app/api/v1/emails/import'
```

> Import email with metadata and values
Import email with metadata and values

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fraw_message=@email.eml\-Frecipient="east-west-trading-co-a34f3a@<example>.rossum.app"\-F'metadata={"source":"rossum","batch_id":"12345"}'\-F'values={"emails_import:customer_id":"CUST-001","emails_import:order_number":"ORD-456"}'\'https://<example>.rossum.app/api/v1/emails/import'
```


```
{"url":"https://<example>.rossum.app/api/v1/tasks/456575"}
```

POST /v1/emails/import
Import an email as raw data. Calling this endpoint starts an asynchronous process of creating
an email object and importing its contents to the specified recipient inbox in Rossum. This endpoint
can be used only byadminandorganization_group_adminroles and email can be imported only to
inboxes within the organization. The caller of this endpoint will be specified as thecreatorof the email.
The email sender specified in thefromheader will still receive any automated notifications targeted to the
email recipients.

Key | Type | Required | Description
--- | --- | --- | ---
raw_message | bytes | true | Raw email data.
recipient | string | true | Email address of the inbox where the email will be imported.
metadata | object | false | JSON object with metadata to be set on created annotations.
values | object | false | JSON object with values to be set on created annotations. All keys must start with theemails_import:prefix (e.g.,emails_import:customer_id).


#### Response

Import email endpoint is asynchronous and response contains created task url. Further information about
the import status may be acquired by retrieving the email object or the task (for more information, please refer totask)
Example import response

```
{
  "url": "https://example.rossum.app/api/v1/tasks/456575"
}
```


### Send email

> Send email

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"to": [{"email": "jack@east-west-trading.com"}], "queue": "https://<example>.rossum.app/api/v1/queues/145300", "template_values": {"subject": "Some subject", "message": "<b>Hello!</b>"}}'\'https://<example>.rossum.app/api/v1/emails/send'
```

Send email to specified recipients. The number of emails that can be sent is limited (10 for trials accounts).

Key | Type | Required | Description
--- | --- | --- | ---
to* | list[email_address_object] |  | List that contains information about recipients.
cc* | list[email_address_object] |  | List that contains information about recipients of carbon copy.
bcc* | list[email_address_object] |  | List that contains information about recipients of blind carbon copy.
template_values | object | false | Values to fill in the email template, it should always containsubjectandmessagekeys. See below for description.
queue | URL | true | Link to email-related queue.
related_annotations | list[URL] | false | List of links to email-related annotations.
related_documents | list[URL] | false | List of URLs to email-related documents (on the top ofrelated_annotationsdocuments which are linked automatically).
attachments | object | false | Keys are attachment types (currently onlydocumentskey is supported), value is list of URL.
parent_email | URL | false | Link to parent email.
reset_related_annotations_email_thread | bool | false | Update related annotations, so that theiremail threadmatches the one of the email object created.
labels | list[string] | false | List ofemail labels.
email_template | URL | false | Link to the email template that was used for the email creation. If specified, the email will be included in theemail templates stats.

*At least one email into,cc,bccmust be filled. The total number of recipients (to,ccandbcctogether) cannot exceed 40.
If the related annotation hasnullemail thread, it will be linked to the email thread related to the email created.
emailobject consists of names and email addresses:

Key | Type | Required | Description
--- | --- | --- | ---
email | email | true | Email address, e.g.john.doe@example.com
name | string | false | Name related to the email, e.g.John Doe


#### Template values

Objecttemplate_valuesis used to create an outgoing email. Keysubjectis used to fill an email subject andmessageis used to fill a body of the email (it may contain a subset of html).
Values may contain other placeholders that are either built-in (see below) or specified in thetemplate_valuesobject as well. For placeholders referring to annotations, the annotations fromrelated_annotationsattribute are used for filling in correct values.
> Example of template_values
Example of template_values

```
{..."template_values":{"subject":"Document processed","message":"<p>The document was processed.<br>{{user_name}}<br>Additional notes: {{note}}</p>","note":"No issues found"}...}
```


Placeholder | Description | Can be used in automation
--- | --- | ---
organization_name | Name of the organization. | True
app_url | App root url | True
user_name | Username of the user sending the email. | False
current_user_fullname | Full name of user sending the email. | False
current_user_email | Email address of the user sending the email. | False
parent_email_subject | Subject of the email we are replying to. | True
sender_email | Email address of the author of the incoming email. | True
annotation.document.original_file_name | Filenames of the documents belonging to the related annotation(s) | True
annotation.content.value.{schema_id} | Content value of datapoints from email related annotation(s) | True
annotation.id | Ids of the related annotation(s) | True
annotation.url | Urls of the related annotation(s) | True
annotation.assignee_email | Emails of the assigned users to the related annotation(s) | True

> Example request data

```
{"to":[{"name":"John Doe","email":"john.doe@rossum.ai"}],"template_values":{"subject":"Rejected!: {{parent_email_subject}}","message":"<p>Dear user,<br>Error occurred!<br><br>Note: {{rejection_note}}. Occurred on your document issued at {{ annotation.content.value.date_issue }}.<br>Yours, Rossum</p>","rejection_note":"There is no invoice id!"},"annotations":["https://<example>.rossum.app/api/v1/annotations/123"],"attachments":{"documents":["https://<example>.rossum.app/api/v1/documents/123"]}}
```


#### Response

Returns created email link.

### Get email counts

> Get email counts

```
curl-XGET-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/emails/counts'
```


```
{"incoming":{"total":12,"no_documents":5,"recent_with_no_documents_not_replied":2,"rejected":1,"recent_filtered_out_documents":2}}
```

GET /v1/emails/counts
Retrieve counts of emails grouped based on status of extracted annotations.
Supports the same filters aslist emailsendpoint.

#### Response

Returns object which under theincomingkey contains object with email counts computed based on the status of extracted documents

Attribute | Type | Description
--- | --- | ---
total | integer | Total number of emails
no_documents | integer | Number of emails containing no attachment which was processed by Rossum
recent_with_no_documents_not_replied | integer | Number of emails arrived in the last 14 days with no attachment processed by Rossum, not withrejectedlabel and without any reply (i. e. email has no relatedchildrenemails - seeemail docs).
rejected | integer | Number of emails containing at least one document inrejectedstatus (seedocument lifecycle) or withrejectedlabel.
recent_with_filtered_out_documents | integer | Number of emails arrived in the last 14 days containing one or more automatically rejected attachment by Rossum smart inbox (rules for email attachment filtering is definedhere).


### Email content

GET /emails/<id>/content
Retrieve content of email.

#### Response


### Email notifications management

> Unsubscribe from automatic email notifications
Unsubscribe from automatic email notifications

```
curl-XGET'https://<example>.rossum.app/api/v1/emails/subscription?content=eyJldmVudCI6ImRvY3VtZW50X3JlY2VpdmVkIiwiZW1haWwiOiJqaXJpLmJhdWVyQHJvc3N1bS5haSIsIm9yZ2FuaXphdGlvbiI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODAwMC92MS9vcmdhbml6YXRpb25zLzEifQ&signature=LhgMR01vQ9NAsvAtOKifZpaYBi20vkhOK-Cm7HT1Cqs&subscribe=false'
```


```
<!DOCTYPE html>...</html>
```

GET /v1/emails/subscription?subscribe=false
Enable or disable subscription to automatic email notifications sent by Rossum.

Query parameter | Type | Default | Required | Description
--- | --- | --- | --- | ---
signature | string |  | true | Signature used to sign the content (generated by our backend).
content | string |  | true | Signed content of the payload (generated by our backend).
subscribe | boolean | true | false | Designates whether the subscription is enabled or disabled.


#### Response


### Email tracking events

> Email tracking events
Email tracking events

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"payload": "ORSXG5DTFVZHVZLSFZQG6Y3BNQ5DC===", "signature": "nGoqalaYlSMFiCPmJDPWaiN3FLEm_cPbxA4mrgqodpk", "link": "https://rossum.ai", "event": "click"}'\'https://<example>.rossum.app/api/v1/email_tracking_events'
```

POST /v1/email_tracking_events
Rossum has the ability to track email events:send,delivery,open,click,bouncefor sent emails.

Key | Type | Required | Description
--- | --- | --- | ---
payload | string | True | Encrypted email, domain and organization ID.
event | string | True | Actions performed on the sent email: bounce, send, delivery, open, click.
link | URL | False | The link from the email body that the user clicked on.
signature | string | True | Signature used to sign the encrypted domain (generated by our backend).


#### Response


## Email Template

> Example email template object
Example email template object

```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","triggers":["https://<example>.rossum.app/api/v1/triggers/500","https://<example>.rossum.app/api/v1/triggers/600"],"type":"custom","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","automate":true}
```

An email template object represents templates one can choose from when sending an email from Rossum.

Attribute | Type | Default | Required | Description | Read-only
--- | --- | --- | --- | --- | ---
id | integer |  |  | Id of the email template | true
url | URL |  |  | URL of the email template | 
name | string |  | true | Name of the email template | 
queue | URL |  | true | URL of the associated queue | 
organization | URL |  |  | URL of the associated organization | 
triggers | list[URL] |  |  | URLs of the linked triggers.Read more | 
type | string | custom |  | Type of the email template (seeemail template types) | 
subject | string | "" |  | Email subject | 
message | string | "" |  | HTML subset of text email section | 
enabled | bool | true |  | (Deprecated) Useautomateinstead | 
automate | bool | true |  | True if user wants to send email automatically on the action, seetypes | 
to* | list[email_address_object] | [] |  | List that contains information about recipients. | 
cc* | list[email_address_object] | [] |  | List that contains information about recipients of carbon copy. | 
bcc* | list[email_address_object] | [] |  | List that contains information about recipients of blind carbon copy. | 

*The total number of recipients (to,ccandbcctogether) cannot exceed 40.

#### Email Template Types

Email Template objects can have one of the following types. Only templates with typesrejectionandcustomcan be manually created and deleted.

Template type name | Description
--- | ---
rejection | Template for a rejection email
rejection_default | Default template for a rejection email
email_with_no_processable_attachments | Template for a reply to an email with no attachments
custom | Custom email template


#### Default Email templates

Every newly created queue triggers a creation of five default email templates with default messages and subjects.

```
[{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"Annotation status change - confirmed","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Verified documents: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Your documents have been checked by annotator.<br><br>{{ document_list }}<br><br>Regards</p>","type":"custom","triggers":["https://<example>.rossum.app/api/v1/triggers/456"],"automate":false,"to":[{"email":"{{sender_email}}"}]},{"id":1235,"url":"https://<example>.rossum.app/api/v1/email_templates/1235","name":"Annotation status change - exported","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Documents exported: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Your documents have been successfully exported.<br><br>{{ document_list }}<br><br>Regards</p>","type":"custom","triggers":["https://<example>.rossum.app/api/v1/triggers/457"],"automate":false,"to":[{"email":"{{sender_email}}"}]},{"id":1236,"url":"https://<example>.rossum.app/api/v1/email_templates/1236","name":"Annotation status change - received","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Documents received: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Your documents have been successfully received.<br><br>{{ document_list }}<br><br>Regards</p>","type":"custom","triggers":["https://<example>.rossum.app/api/v1/triggers/458"],"automate":false,"to":[{"email":"{{sender_email}}"}]},{"id":1237,"url":"https://<example>.rossum.app/api/v1/email_templates/1237","name":"Default rejection template","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"Rejected document {{parent_email_subject}}","message":"<p>Dear sender,<br><br>The attached document has been rejected.<br><br><br>Best regards,<br>{{ user_name }}</p>","type":"rejection_default","triggers":[],"automate":true,"to":[{"email":"{{sender_email}}"}]},{"id":1238,"url":"https://<example>.rossum.app/api/v1/email_templates/1238","name":"Email with no processable attachments","queue":"https://<example>.rossum.app/api/v1/queues/501","organization":"https://<example>.rossum.app/api/v1/organizations/123","subject":"No processable documents: {{ parent_email_subject }}","message":"<p>Dear sender,<br><br>Unfortunately, we have not received any document in the email that we can process. Please send a corrected version if appropriate.<br><br>Regards</p>","type":"email_with_no_processable_attachments","triggers":["https://<example>.rossum.app/api/v1/triggers/459"],"automate":false,"to":[{"email":"{{sender_email}}"}]}]
```


#### Email template rendering

Email templates supportDjango Template Variables.
Please note that only simple variables are supported. Filters and the.lookup are not. A template such as:

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


```
{% if subject %}
  The subject is Hello.
  {% endif %}
  The message is .
```


### List all email templates

> List all email templates
List all email templates

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_templates'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","type":"custom","automate":true}]}
```

GET /v1/email_templates
Retrieve all email template objects.
Supported filters:id,queue,type,name
Supported ordering:id,name
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofemail templateobjects.

### Create new email template object

> Create new email template in queue4321
Create new email template in queue4321

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "name": "My Email Template", "subject": "My Email Template Subject", "message": "<p>My Email Template Message</p>", "type": "custom"}'\'https://<example>.rossum.app/api/v1/email_templates'
```


```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","type":"custom"}
```

POST /v1/email_templates
Create new email template object.

#### Response

Returns newemail templateobject.

### Retrieve an email template object

> Get email template object1234
Get email template object1234

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_templates/1234'
```


```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"My Email Template Subject","message":"<p>My Email Template Message</p>","type":"custom","automate":true}
```

GET /v1/email_templates/{id}
Get an email template object.

#### Response

Returnsemail templateobject.

### Update an email template

> Update email template object1234
Update email template object1234

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "subject": "Some new subject"}'\'https://<example>.rossum.app/api/v1/email_templates/1234'
```


```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/email_templates/1234","name":"My Email Template","queue":"https://<example>.rossum.app/api/v1/queues/4321","organization":"https://<example>.rossum.app/api/v1/queues/210","subject":"Some new subject","message":"<p>My Email Template Message</p>","type":"custom","automate":true}
```

PUT /v1/email_templates/{id}
Update email template object.

#### Response

Returns updatedemail templateobject.

### Update part of an email template

> Update subject of email template object1234
Update subject of email template object1234

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"subject": "Some new subject"}'\'https://<example>.rossum.app/api/v1/email_templates/1234'
```


```
{"id":1234,"subject":"Some new subject",...}
```

PATCH /v1/email_templates/{id}
Update part of an email template object.

#### Response

Returns updatedemail templateobject.

### Delete an email template

> Delete email template object1234
Delete email template object1234

```
curl-XDELETE'https://<example>.rossum.app/api/v1/email_templates/1234'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
```

DELETE /v1/email_templates/{id}
Delete an email template object.

#### Response


### Get email templates stats

> Get stats for all email templates from queue with id478
Get stats for all email templates from queue with id478

```
curl-XGET'https://<example>.rossum.app/api/v1/email_templates/stats?queue=478'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
```


```
{"pagination":{"total":6,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/email_templates/2","manual_count":12,"automated_count":190},{"url":"https://<example>.rossum.app/api/v1/email_templates/3","manual_count":87,"automated_count":0},...]}
```

GET /v1/email_templates/stats
Get stats for email templates.

#### Response

Returns paginated response with a list of following objects

Attribute | Type | Description
--- | --- | ---
url | URL | Link of the email template.
manual_count | integer | Number of manually sent emails in the last 90 days based on given email template.
automated_count | integer | Number of automatically sent emails in the last 90 days based on given email template.

Supports the same filters aslist email templatesendpoint.

### Render email template

> Render email template221
Render email template221

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"parent_email": "https://<example>.rossum.app/api/v1/emails/1234", "document_list": ["https://<example>.rossum.app/api/v1/documents/2314"], "to": [{"email": "{{ current_user_email }}"}]}'\'https://<example>.rossum.app/api/v1/email_templates/221/render'
```


```
{"to":[{"email":"satisfied.customer@rossum.ai"}],"cc":[],"bcc":[],"subject":"My Email Template Subject: Rendered Parent Email Subject","message":"<p>My Email Template Message from user@example.com</p>"}
```

POST /v1/email_templates/{id}/render
The rendered email template can be requested via therenderendpoint with the following attributes:

Attribute | Type | Default | Required | Description
--- | --- | --- | --- | ---
to* | list[email_address_object] | [] | false | List that contains information about recipients to be rendered.
cc* | list[email_address_object] | [] | false | List that contains information about recipients of carbon copy to be rendered.
bcc* | list[email_address_object] | [] | false | List that contains information about recipients of blind carbon copy to be rendered.
parent_email | URL |  | false | Link toparent_email.
document_list | list[URL] | [] | false | List ofdocument's URLs to simulate sending of documents over email into Rossum
annotation_list | list[URL] | [] | false | List ofannotation's URLs to use for rendering values for annotation.content placeholders
template_values | object | {} | false | Values to fill in the email template.Read more.

*The total number of recipients (to,ccandbcctogether) cannot exceed 40.
Inside theto,ccandbccattributes template variables can be used instead of the email field of theemail_address_object. See thelist of built-in placeholdersfor available variables.

#### Response

Returns rendered message and subject of an email template

Attribute | Type | Description
--- | --- | ---
to | list[email_address_object] | List that contains rendered information about recipients.
cc | list[email_address_object] | List that contains rendered information about recipients of carbon copy.
bcc | list[email_address_object] | List that contains rendered information about recipients of blind carbon copy.
message | string | Rendered email template's message.
subject | string | Rendered email template's subject.


## Email Thread

> Example email thread object
Example email thread object

```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":false,"root_email_read":false,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z","labels":[],"annotation_counts":{"annotations":4,"annotations_processed":2,"annotations_purged":0,"annotations_rejected":1,"annotations_unprocessed":1}}
```

An email thread object represents thread of related objects in Rossum's inbox.

Attribute | Type | Required | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the email thread. | true
url | URL |  | URL of the email thread. | 
organization | URL |  | URL of the associated organization. | true
queue | URL |  | URL of the associated queue. | true
root_email | URL |  | URL of the associated root email (first incoming email in the thread). | true
has_replies | boolean |  | True if the thread has more than one incoming emails. | true
has_new_replies | boolean |  | True if the thread has unread incoming emails. | 
root_email_read | boolean |  | True if the root email has been opened in Rossum UI at least once. | true
created_at | datetime |  | Timestamp of the creation of email thread (inherited from arrived_at timestamp of the root email). | true
last_email_created_at | datetime |  | Timestamp of the most recent email in this email thread. | true
subject | string |  | Subject of the root email. | true
from | object |  | Information about sender of the root email containing keysemailandname. | true
labels | list[string] |  | This attribute is intended forINTERNALuse only and may be changed without notice. List of email thread labels set by root email. If root email is rejected and no other incoming emails are in thread, labels field is set to[rejected]. Labels is an empty list in all the other cases. | true
annotation_counts | object |  | This attribute is intended forINTERNALuse only and may be changed without notice. Information about how many annotations were extracted from all emails in the thread and in which state they currently are | true


#### Thread Annotation counts object

This object stores numbers of annotations extracted from all emails in given email thread.

Attribute | Type | Description | Annotation status
--- | --- | --- | ---
annotations | integer | Total number of annotations | Any
annotations_processed | integer | Number of processed annotations | exported,deleted,purged,split
annotations_purged | integer | Number of purged annotations | purged
annotations_unprocessed | integer | Number of not yet processed annotations | importing,failed_import,to_review,reviewing,confirmed,exporting,postponed,failed_export
annotations_rejected | integer | Number of rejected annotations | rejected
related_annotations | integer | Total number of related annotations | Any


### List all email threads

> List all email threads
List all email threads

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_threads'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":false,"root_email_read":false,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...},...]}
```

GET /v1/email_threads
Retrieve all email thread objects.

#### Supported filters

Email threads support following filters:

Filter name | Type | Description
--- | --- | ---
has_root_email | boolean | Filter only email threads with a root email.
has_replies | boolean | Filter only email threads with two and more emails with typeincoming
queue | integer | Filter only email threads associated with given queue id (or multiple ids).
has_new_replies | boolean | Filter only email threads with unread emails with typeincoming
created_at_before | datetime | Filter only email threads with root email created before given timestamp.
created_at_after | datetime | Filter only email threads with root email created after given timestamp.
last_email_created_at_before | datetime | Filter only email threads with the last email in the thread created before given timestamp.
last_email_created_at_after | datetime | Filter only email threads with the last email in the thread created after given timestamp.
recent_with_no_documents_not_replied | boolean | Filter only email threads with root email that arrived in the last 14 days with no attachment processed by Rossum, excluding those: withrejectedlabel, without any reply and when root email has been read.


#### Supported ordering

Email threads support following ordering:id,created_at,last_email_created_at,subject,from__email,from__name,queue
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofemail threadobjects.

### Retrieve an email thread

> Get email thread object1244
Get email thread object1244

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/email_threads/1244'
```


```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":false,"root_email_read":false,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...}
```

GET /v1/email_threads/{id}
Get an email thread object.

#### Response

Returnsemail threadobject.

### Update an email thread

> Update email thread object1244
Update email thread object1244

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"root_email": "https://<example>.rossum.app/api/v1/emails/5432", "has_new_replies": "True"}'\'https://<example>.rossum.app/api/v1/email_threads/1244'
```


```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":true,"root_email_read":true,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...}
```

PUT /v1/email_threads/{id}
Update email thread object.

#### Response

Returns updatedemail threadobject.

### Update part of an email thread

> Update flag has_new_responses of email thread object1244
Update flag has_new_responses of email thread object1244

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"has_new_replies": "True"}'\'https://<example>.rossum.app/api/v1/emails/1244'
```


```
{"id":1244,"url":"https://<example>.rossum.app/api/v1/email_threads/1244","organization":"https://<example>.rossum.app/api/v1/organizations/132","queue":"https://<example>.rossum.app/api/v1/queues/4857","root_email":"https://<example>.rossum.app/api/v1/emails/5432","has_replies":false,"has_new_replies":true,"root_email_read":true,"last_email_created_at":"2021-11-01T18:02:24.740600Z","subject":"Root email subject","from":{"email":"satisfied.customer@rossum.ai","name":"Satisfied Customer"},"created_at":"2021-06-10T12:38:44.866180Z",...}
```

PATCH /v1/email_threads/{id}
Update part of email thread object.

#### Response

Returns updatedemail threadobject.

### Get email thread counts

> Get email thread counts
Get email thread counts

```
curl-XGET-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/email_threads/counts'
```


```
{"with_replies":5,"with_new_replies":3,"recent_with_no_documents_not_replied":2}
```

GET /v1/email_threads/counts
Retrieve counts of email threads.
Supports the same filters aslist email threadsendpoint.

#### Response

Returns object with email thread counts.

Attribute | Type | Description
--- | --- | ---
with_replies | integer | Number of email threads containing two or moreincomingemails
with_new_replies | integer | Number of emails threads containing unreadincomingreplies.
recent_with_no_documents_not_replied | integer | Number of email threads with root email that arrived in the last 14 days without any attachments processed by Rossum, excluding those: withrejectedlabel, without any reply (email thread contains only this email) and when root email has been read.


## Generic Engine

> Example generic engine object
Example generic engine object

```
{"id":3000,"url":"https://<example>.rossum.app/api/v1/generic_engines/3000","name":"Generic engine","description":"AI engine trained to recognize data for the specific data capture requirement","documentation_url":"https://rossum.ai/help/faq/generic-ai-engine/","schema":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000"}
```

A Generic Engine object holds specification of training setup for Rossum trained Engine.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the generic engine | true
url | URL |  | URL of the generic engine | true
name | string |  | Name of the generic engine | 
description | string |  | Description of the generic engine | 
documentation_url | url | null | URL of the generic engine's documentation | 
schema | url | null | Relatedgeneric engine schema | 


### List all generic engines

> List all generic engines
List all generic engines

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engines'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":3000,"url":"https://<example>.rossum.app/api/v1/generic_engines/3000","name":"Generic engine","description":"AI engine trained to recognize data for the specific data capture requirement","documentation_url":"https://rossum.ai/help/faq/generic-ai-engine/","schema":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000"}]}
```

GET /v1/generic_engines
Retrieve all generic engine objects.

#### Response

Returnspaginatedresponse with a list ofgeneric engineobjects.

### Retrieve a generic engine

> Get generic engine object3000
Get generic engine object3000

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engines/3000'
```


```
{"id":3000,"url":"https://<example>.rossum.app/api/v1/generic_engines/3000","name":"Generic engine","description":"AI engine trained to recognize data for the specific data capture requirement","documentation_url":"https://rossum.ai/help/faq/generic-ai-engine/","schema":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000"}
```

GET /v1/generic_engines/{id}
Get a generic engine object.

#### Response

Returnsgeneric engineobject.

## Generic Engine Schema

> Example generic engine schema object
Example generic engine schema object

```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000","content":{"training_queues":[],"fields":[{"category":"datapoint","engine_output_id":"document_id","type":"string","label":"label text","description":"description text","trained":true,"sources":[]},{"category":"multivalue","engine_output_id":"my_cool_ids","label":"label text","description":"description text","type":"freeform","trained":false,"children":{"category":"datapoint","engine_output_id":"my_cool_id","type":"enum","label":"label text","description":"description text","trained":false,"sources":[]}},{"category":"multivalue","engine_output_id":"date_timezone_table","label":"label text","description":"description text","type":"grid","trained":true,"children":{"category":"tuple","children":[{"category":"datapoint","engine_output_id":"date","type":"date","label":"label text","description":"description text","trained":true,"sources":[]},{"category":"datapoint","engine_output_id":"timezone","type":"string","label":"label text","description":"description text","trained":true,"sources":[]}]}}]}}
```

An engine schema is an object which describes what fields are available in the engine. Do not confuse engine schema withDocument Schema.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the generic engine schema | true
url | URL |  | URL of the generic engine schema | true
content | object |  | See Dedicated Engine Schema's description of thecontent structure | 


### List all generic engine schemas

> List all generic engine schemas
List all generic engine schemas

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engine_schemas'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":6000,"url":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}]}
```

GET /v1/generic_engine_schemas
Retrieve all generic engine schema objects.

#### Response

Returnspaginatedresponse with a list ofgeneric engine schemaobjects.

### Retrieve a generic engine schema

> Get generic engine schema object6000
Get generic engine schema object6000

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/generic_engine_schemas/6000'
```


```
{"id":6000,"url":"https://<example>.rossum.app/api/v1/generic_engine_schemas/6000","content":{"training_queues":[...],"fields":[...]}}
```

GET /v1/generic_engine_schemas/{id}
Get a generic engine schema object.

#### Response

Returnsgeneric engine schemaobject.

## Hook

> Example hook object of type webhook
Example hook object of type webhook

```
{"id":1500,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Change of Status","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"sideload":["queues"],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.east-west-trading.com/api/hook1?strict=true","secret":"secret-token","insecure_ssl":false,"client_ssl_certificate":"-----BEGIN CERTIFICATE-----\n...","timeout_s":30,"retry_count":4,"app":{"display_mode":"drawer","url":"https://myq.east-west-trading.com/api/hook1?strict=true","settings":{},}},"test":{"saved_input":{...}},"extension_source":"custom","settings":{},"settings_schema":{"type":"object","properties":{}},"secrets":{},"secrets_schema":{"type":"object","properties":{}},"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":"https://<example>.rossum.app/api/v1/hook_templates/998877","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

> Example hook object of type function
Example hook object of type function

```
{"id":1500,"type":"function","url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Empty function","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"sideload":["modifiers"],"active":true,"events":["annotation_status.changed"],"config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};","timeout_s":30,"retry_count":4,"app":{"display_mode":"drawer","url":"https://myq.east-west-trading.com/api/hook1?strict=true","settings":{},}},"token_owner":"https://<example>.rossum.app/api/v1/users/12345","token_lifetime_s":1000,"test":{"saved_input":{...}},"status":"ready","extension_source":"custom","settings":{},"settings_schema":{"type":"object","properties":{}},"secrets":{},"secrets_schema":{"type":"object","properties":{}},"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":"https://<example>.rossum.app/api/v1/hook_templates/998877","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

A hook is an extension of Rossum that is notified when specific event occurs.
A hook object is used to configure what endpoint or function is executed and
when. For an overview of other extension options seeExtensions.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the hook | true
type | string | webhook | Hook type. Possible values:webhook,function | 
name | string |  | Name of the hook | 
url | URL |  | URL of the hook | true
queues | list[URL] |  | List of queues that use hook object. | 
run_after | list[URL] |  | List of all hooks that has to be executed before running this hook. | 
active | bool |  | If set totruethe hook is notified. | 
events | list[string] |  | List of events, when the hook should be notified. For the list of events seeWebhook events. | 
sideload | list[string] | [] | List of related objects that should be included in hook request. For the list of possible sideloads seeWebhook events. | 
metadata | object | {} | Client data. | 
config | object |  | Configuration of the hook. | 
token_owner | URL |  | URL of a user object. If present, an API access token is generated for this user andsent to the hook. Users with organization group admin cannot be set as token_owner. Ifnull, token is not generated. | 
token_lifetime_s | integer | null | Lifetime number of seconds forrossum_authorization_token(min=0, max=7200). This setting will ensure the token will be valid after hook response is returned. Ifnull, default lifetime of600is used. | 
test | object | {} | Input saved for hook testing purposes, seeTest a hook | 
description | string |  | Hook description text. | 
extension_source | string | custom | Import source of the extension. | 
settings | object | {} | Specific settings that will be included in the payload when executing the hook. Field is validated with json schema stored insettings_schemafield. | 
settings_schema | object | null | [BETA]JSON schema forsettingsfield validation. | 
secrets | object | {} | Specific secrets that are stored securely encrypted. The values are merged into the hook execution payload. Field is validated with json schema stored insecrets_schemafield.  (write only) | 
secrets_schema | object | JSON schema | [BETA]JSON schema forsecretsfield validation. | 
guide | string |  | Description how to use the extension. | 
read_more_url | URL |  | URL address leading to more info page. | 
extension_image_url | URL |  | URL address of extension picture. | 
hook_template | URL | null | URL of the hook template used to create the hook | 
created_by | URL | null | URL of the hook creator. Might benullfor hooks created before April 2025. | true
created_at | datetime | null | Date of hook creation. Might benullfor hooks created before April 2025. | true
modified_by | URL | null | URL of the last hook modifier | true
modified_at | datetime | null | Date of last modification | true


#### Config attribute

Config attribute allows to specify per-type configuration.

Attribute | Type | Default | Description
--- | --- | --- | ---
url | URL |  | URL of the webhook endpoint to call
secret | string |  | (optional) If set, it is used to create a hash signature with each payload. For more information seeValidating payloads from Rossum
insecure_ssl | bool | false | Disable SSL certificate verification (only use for testing purposes).
client_ssl_certificate | string |  | Client SSL certificate used to authenticate requests. Must be PEM encoded.
client_ssl_key | string |  | Client SSL key (write only). Must be PEM encoded. Key may not be encrypted.
private | bool | false | (optional) If set, theurlandsecretvalues become hidden and immutable once the hook is created. The value of this flag cannot be changed tofalseonce set.
schedule | object | {} | Specific configuration for hooks of invocation.scheduled event and action interval. Seeschedule
timeout_s | int | 30 | Webhook call timeout in seconds. For non-interactive webhooks only (min=0, max=60).
retry_count | int | 4 | Number of times the webhook call is retried in case of failure. For non-interactive webhooks only (min=0, max=4).
max_polling_time_s | int | 300 | The maximum polling time in seconds forasynchronous webhooks(min=1, max=3600). It is possible to configure this value only forupload.createdandinvocation.scheduledevents. For other non-interactive events the default value is used.
retry_after_polling_failure | bool | true | If set totrue, the original webhook call is retried in case the polling fails. See theasynchronous webhookssection for more details. Possible to configure only forupload.createdandinvocation.scheduledevents. For other non-interactive events the default value is used.
app | obj |  | (deprecated) (optional) Configuration of the app
payload_logging_enabled | bool | false | (optional) If set to False, hook payload is omited from hook logs feature accessible via UI
retry_on_any_non_2xx | bool | false | (optional) Disabling this option results in retrying only on these response statuses: [408, 429, 500, 502, 503, 504]


Attribute | Type | Default | Description
--- | --- | --- | ---
runtime | string |  | Runtime used to execute code. Allowed values:nodejs22.xorpython3.12.
code | string |  | String-serialized source code to be executed
third_party_library_pack | string | default | Set of libraries to be included in execution environment of the function, seedocumentation belowfor details.
private | bool | false | (optional) If set, theruntime,codeandthird_party_library_packvalues become hidden and immutable once the hook is created. The value of this flag cannot be changed tofalseonce set.
schedule | obj | {} | Specific configuration for hooks of invocation.scheduled event and action interval. Seeschedule
timeout_s | int | 30 | Function call timeout in seconds. For non-interactive functions only (min=0, max=60)
memory_size_mb | int | 256 | Function memory limit (min=128, max=256). The limit can be increased upon request.
retry_count | int | 4 | Number of times the function call is retried in case of failure. For non-interactive functions only (min=0, max=4).
app | obj |  | (deprecated) (optional) Configuration of the app
payload_logging_enabled | bool | false | (optional) If set to False, hook payload is omited from hook logs feature accessible via UI


#### Schedule object

Scheduleobject contains the following additional event-specific attributes.Cronobject interval can't be shorter than every 10 minutes.

Key | Type | Description
--- | --- | ---
cron | object | Used to set interval withcron expressionin UTC timezone.


#### App object (deprecated)

TheAppobject contains the following attributes.

Key | Type | Default | Description | Required
--- | --- | --- | --- | ---
url | URL |  | URL of the app that will be embedded in Rossum UI. | True
settings | object |  | Settings of the app that can be used for further customization of configuration app (such as UI schema etc.) | False
display_mode | string | drawer | Display mode of the app | 

Currently, there are two display modes supported.

display_mode | Description
--- | ---
drawer | opens a drawer with embedded URL
fullscreen | opens an embedded URL in full-screen overlay

Libraries available in the execution environment can be configured via optionthird_party_library_pack.
Please note that functions with third party libraries need up to 30 seconds to update the code.
Let us knowif you need any additional libraries.

Value | Type | Description
--- | --- | ---
null | object | Only standard Python Standard Library is available
default | string | Contains additional librariesrossum,requests,jmespath,xmltodict,pydantic,pandas,httpx,boto3andbotocore


Value | Type | Description
--- | --- | ---
null | object | Only Node.js Built-in Modules are available
default | string | Contains additional librariesnode-fetch,https-proxy-agentandlodash


Attribute | Type | Description | Read-only
--- | --- | --- | ---
status | string | Status indicates whether the function is ready to be invoked or modified. Possible values areready,pendingorfailed. While the state ispending, invocations and other API actions that operate on the function return status 400. It is recommended to resave function forfailedstate. | True

This value indicates where the hook has been imported from.

Value | Description
--- | ---
custom | The Hook has been imported and set up by the user.
rossum_store | A preconfigured Hook has been imported from an extension store.

The content ofsecretsis stored encrypted and is write-only in the API. There is an additionalsecrets_schemaproperty to provide a JSON schema forsecretsvalidation.
To getsecretsas a list of keys, please refer toRetrieve list of secrets keys
JSON schema for the hooksecretsproperties. Schema needs to includeadditionalProperties. This needs to be either set tofalse(as shown in the example), so no additional properties than the ones specified in this schema are allowed forsecretsfield, or set to an object with"type": "string"property (as shown in the default value), to ensure all additional properties are of type string. More onadditionalPropertiescan be found in the officialdocs
> Example of Secrets schema object for validating two secrets properties
Example of Secrets schema object for validating two secrets properties

```
{"type":"object","properties":{"username":{"type":"string","description":"Target system user",},"password":{"type":"string","description":"Target system user password",}},"additionalProperties":false}
```

> Default value of secrets_schema field
Default value of secrets_schema field

```
{"type":"object","additionalProperties":{"type":"string"}}
```

JSON schema for the hooksettingsvalidation.
> Example of Settings schema object for validating two settings properties
Example of Settings schema object for validating two settings properties

```
{"type":"object","properties":{"username":{"type":"string","description":"Target system user",},"password":{"type":"string","description":"Target system user password",}}}
```


### List all hooks

> List all hooks

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Some Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.east-west-trading.com/api/hook1?strict=true","schedule":{"cron":"*/10 * * * *"}},"test":{"saved_input":{...}},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
```

Retrieve all hook objects.
Supported filters:id,name,type,queue,active,config_url,config_app_url,extension_source,events
Supported ordering:id,name,type,active,config_url,config_app_url,events
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofhookobjects.

### List Hook Call Logs

> Get a list of hook call logs
Get a list of hook call logs

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/hooks/logs'
```


```
{"results":[{"timestamp":"2023-09-23T12:00:00.000000Z","request_id":"6166deb3-2f89-4fc2-9359-56cc8e3838e4","event":"annotation_content","action":"updated","annotation_id":1,"queue_id":1,"hook_id":1,"hook_type":"webhook","log_level":"INFO","message":"message","request":"{}","response":"{}","start":"2023-09-23T12:00:00.000000Z","end":"2023-09-23T12:00:00.000000Z","settings":"{}","status":"completed","uuid":"6166deb3-2f89-4fc2-9359-56cc8e3838e4"},{"timestamp":"2023-09-23T12:00:00.000000Z","request_id":"1234abc1-1bg3-4cf2-9876-32aa8e3434a2","event":"email","action":"received","email_id":1,"queue_id":1,"hook_id":1,"hook_type":"webhook","log_level":"INFO","message":"message","request":"{}","response":"{}","start":"2023-09-23T12:00:00.000000Z","end":"2023-09-23T12:00:00.000000Z","settings":"{}","status":"completed","uuid":"1234abc1-1bg3-4cf2-9876-32aa8e3434a2"}]}
```

List all the logs from all running hooks. The logs are sorted by thestarttimestamp in descending order.

Filter name | Type | Description
--- | --- | ---
request_id | string | Match the specifiedrequest_id.
log_level | string | Match the specified log level (or multiple log levels).
hook | integer | Match given the hook id (or multiple ids).
timestamp_before | datetime | Filter for log entries before given timestamp.
timestamp_after | datetime | Filter for log entries after given timestamp.
start_before | datetime | Filter for log entries before given start timestamp.
start_after | datetime | Filter for log entries after given start timestamp.
status | string | Match the log entrystatus(or multiple statuses). Available choices:waiting,running,completed,cancelled,failed.
status_code | integer | Match the responsestatus_code(or multiple).
queue | integer | Match the given queue id (or multiple ids).
annotation | integer | Match the given annotation id (or multiple ids).
email | integer | Match the given email id (or multiple ids).
search | string | Full text filter across all the log entry fields.
page_size | integer | Maximum number of results to return (between 1 and 100, defaults to 100).

The retention policy for the logs is set to 7 days.
For additional info please refer tofilters and ordering.

#### Response

Returns list of thehook logs

### Create a new hook

> Create new hook related to queue8199with endpoint URLhttps://myq.east-west-trading.com
Create new hook related to queue8199with endpoint URLhttps://myq.east-west-trading.com

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Hook", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "config": {"url": "https://myq.east-west-trading.com"}, "events": []}'\'https://<example>.rossum.app/api/v1/hooks'
```


```
{"id":1501,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1501","name":"MyQ Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199"],"run_after":[],"active":true,"events":[],"config":{"url":"https://myq.east-west-trading.com","schedule":{}},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":null,"read_more_url":null,"extension_image_url":null}
```

Create a new hook object.

#### Response

Returns createdhookobject.

### Create a new hook from hook template

> Create new hook using a hook template referencehttps://<example>.rossum.app/api/v1/hook_templates/5
Create new hook using a hook template referencehttps://<example>.rossum.app/api/v1/hook_templates/5

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyT Hook", "hook_template": "https://<example>.rossum.app/api/v1/hook_templates/5", "events": ["annotation_status.changed"]}',"queues":[]\'https://<example>.rossum.app/api/v1/hooks/create'
```


```
{"id":1502,"type":"webhook","url":"https://<example>.rossum.app/api/v1/hooks/1502","name":"MyT Hook","metadata":{},"queues":[],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"private":true},"test":{},"settings":{},"settings_schema":null,"description":"A closed source hook created from an extension store hook template...","extension_source":"rossum_store","guide":null,"read_more_url":null,"extension_image_url":null,"hook_template":"https://<example>.rossum.app/api/v1/hook_templates/5","created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

POST /v1/hooks/create
Create a new hook object with the option to use a referenced hook template as a base.

#### Response

Returns createdhookobject.

### Retrieve a hook

> Get hook object1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500'
```


```
{"id":1500,"url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Some Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.east-west-trading.com/api/hook1?strict=true"},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":null,"created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```


#### Response


### Update a hook

> Update hook object1500
Update hook object1500

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "MyQ Hook (stg)", "queues": ["https://<example>.rossum.app/api/v1/queues/8199"], "config": {"url": "https://myq.stg.east-west-trading.com"}, "events": []} \
  'https://<example>.rossum.app/api/v1/hooks/1500'
```


```
{"id":1500,"url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"MyQ Hook (stg)","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199"],"run_after":[],"active":true,"events":[],"config":{"url":"https://myq.stg.east-west-trading.com"},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":null,"read_more_url":null,"extension_image_url":null,"hook_template":null,"created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```


#### Response

Returns updatedhookobject.

### Update part of a hook

> Update hook URL of hook object1500
Update hook URL of hook object1500

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"config": {"url": "https://myq.stg2.east-west-trading.com"}}'\'https://<example>.rossum.app/api/v1/hooks/1500'
```


```
{"id":1500,"url":"https://<example>.rossum.app/api/v1/hooks/1500","name":"Some Hook","metadata":{},"queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8191"],"run_after":[],"active":true,"events":["annotation_status.changed"],"config":{"url":"https://myq.stg2.east-west-trading.com"},"test":{},"settings":{},"settings_schema":null,"description":"This hook does...","extension_source":"custom","guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg","hook_template":null,"created_by":"https://<example>.rossum.app/api/v1/users/2","created_at":"2020-01-01T09:05:50.213451Z","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

Update part of hook object.

#### Response

Returns updatedhookobject.

### Delete a hook

> Delete hook1500

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500'
```

DELETE /v1/hooks/{id}

#### Response


### Duplicate a hook

> Duplicate existing hook object123
Duplicate existing hook object123

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Duplicate Hook", "copy_secrets": true, "copy_dependencies": true}'\'https://<example>.rossum.app/api/v1/hooks/123/duplicate'
```


```
{"id":124,"name":"Duplicate Hook","url":"https://<example>.rossum.app/api/v1/hooks/124",...}
```

POST /v1/hooks/{id}/duplicate
Duplicate a hook object.hook.queuesis not copied. Duplicated hook is always inactive (hook.active = False).

Attribute | Type | Default | Description
--- | --- | --- | ---
name | string |  | Name of the duplicated hook.
copy_secrets | bool | false | Whether to copy secrets.
copy_dependencies | bool | false | Whether to copy dependencies. If enabled, this option copies the dependency relations of the original hook. It duplicates therun_afterreferences to preserve which hooks the original hook depended on, and it also updates all hooks that previously depended on the original hook to reference the new duplicated one. This ensures that both dependency directions—“runs after” and “is run after by”—are correctly maintained.


#### Response

Returns duplicate ofhookobject.

### Test a hook

> Call webhook1500and display its result
Call webhook1500and display its result

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


```
{"response":{"messages":[],"operations":[]}}
```

> Call serverless function (code may be specified in the request) and display its result
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


```
{"response":{"messages":[],"operations":[]}}
```

POST /v1/hooks/{id}/test
Test a hook with custom payload. Test endpoint will return result generated by the specified Hook which would be normally processed by Rossum.

Attribute | Type | Required | Description
--- | --- | --- | ---
config | object | false | You can override defaultconfigurationof hook being executed. Theruntimeattribute is required for function hook if custom config is set.
payload | object | true | Payload sent to the Hook, please note onlysupportedcombination ofactionandeventcan be passed.


#### Response

Status:200in case of success.409in case the test function is not ready yet -- then request should be retried after 10 seconds.

### Manual hook trigger

> Example data sent forinvocation.manualevent and action with extra arguments
Example data sent forinvocation.manualevent and action with extra arguments

```
curl'https://<example>.rossum.app/api/v1/hooks/789/invoke'-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"SAP_ID": "1234", "DB_COLUMN": "SAP"}'
```

> Example data sent frominvocation.manualhook to your client following the request above
Example data sent frominvocation.manualhook to your client following the request above

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/789","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"my-rossum-importer","password":"secret-importer-user-password"},"action":"manual","event":"invocation","SAP_ID":"1234","DB_COLUMN":"SAP"}
```

POST /v1/hooks/{id}/invoke
Invoke the hook with custom payload. The payload will be added to the standardinvocationevent hook request and sent to the hook. The hook response is returned in the invocation response payload.

#### Payload

Object with properties to be merged into the invocation payload.

#### Response

Status:200in case of success.400in case of not having proper event and action in hook object or non-json response.

### Retrieve list of secrets keys

> Get secret_keys of hook object1500
Get secret_keys of hook object1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500/secrets_keys'
```


```
["secret_key1","secret_key2"]
```

GET /v1/hooks/{id}/secrets_keys
Retrieve all secrets in a list (only keys are retrieved, values are encrypted in DB and aren't possible to obtain via API)

#### Response

Returns list ofhook secretskeys.

### Generate payload for hook

> Generate hook payload for hook object1500
Generate hook payload for hook object1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hooks/1500/generate_payload'
```


```
{"event":"invocation","action":"scheduled"}
```

Users can use this endpoint to test the hook on a payload of specific events and actions.
> Example data forinvocation.scheduledhook
Example data forinvocation.scheduledhook

```
{"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","timestamp":"2020-01-01T00:00:00.000000Z","base_url":"https://<example>.rossum.app","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","hook":"https://<example>.rossum.app/api/v1/hooks/1500","settings":{"example_target_service_type":"SFTP","example_target_hostname":"sftp.elis.rossum.ai"},"secrets":{"username":"[redacted...]","password":"[redacted...]"},"action":"schedule","event":"invocation"}
```

POST /v1/hooks/{id}/generate_payload

Attribute | Type | Required | Description
--- | --- | --- | ---
action | string | true | Hook'saction
event | string | true | Hook'sevent
annotation | URL |  | URL of related Annotation object. Required for annotation_status and annotation_content events.
previous_status | enum |  | A previous status of the document. SeeDocument Lifecyclefor a list of supported values. Required for annotation_status and annotation_content events.
status | enum |  | Status of the document. SeeDocument Lifecyclefor a list of supported values. Required for annotation_status and annotation_content events.
email | URL |  | URL of the arriving email. Required for email event.
upload | URL |  | URL of an upload instance. Required for upload event.


#### Response

Returnshookpayload for specific event and action. The token used for calling the endpoint is returned asrossum_authorization_tokenregardless of thetoken_ownerof the hook.
Values insecretsare redacted as shown in the example for security reasons. The payload for email events from this endpoint may differ from the original hook payload in the file ids,
height, width, and format of email addresses in headers.

## Hook Template

> Example hook template object
Example hook template object

```
{"url":"https://<example>.rossum.app/api/v1/hook_templates/1","metadata":{},"events":["annotation_status.changed"],"test":{"hook":"https://<example>.rossum.app/api/v1/hooks/789","event":"annotation_status","action":"changed","document":{...},"settings":{"rules":[{"value":"receipt","schema_id":"document_type","target_queue":128153,"target_status":"to_review","trigger_status":"to_review"},{"value":"invoice","schema_id":"document_type","target_queue":108833,"target_status":"to_review","trigger_status":"to_review"}]},"timestamp":"2020-01-01T00:00:00.000000Z","annotation":{...},"request_id":"ae7bc8dd-73bd-489b-a3d2-f5514b209591","rossum_authorization_token":"1024873d424a007d8eebff7b3684d283abdf7d0d","base_url":"https://<example>.rossum.app"},"settings":{"rules":[{"value":"receipt","schema_id":"document_type","target_queue":128153,"target_status":"to_review","trigger_status":"to_review"},{"value":"invoice","schema_id":"document_type","target_queue":108833,"target_status":"to_review","trigger_status":"to_review"}]},"settings_description":[{"name":"Rules","description":"List of rules to be applied."},{"name":"Target queue","description":"The ID of the queue where the document will move."}],"name":"Document sorting","type":"function","config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};""schedule":{"cron":"*/10 * * * *"}},"sideload":["queues"],"description":"Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.","extension_source":"rossum_store","settings_schema":null,"secrets_schema":null,"store_description":"<p>Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.</p>","external_url":"","use_token_owner":true,"install_action":"copy","token_lifetime_s":null,"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg"}
```

Hook template is a definition of hook in Rossum extension store.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the hook | true
type | string | webhook | Hook type. Possible values:webhook,function | 
name | string |  | Name of the hook | 
url | URL |  | URL of the hook | true
events | list[string] |  | List of events, when the hook should be notified. For the list of events seeWebhook events. | 
sideload | list[string] | [] | List of related objects that should be included in hook request. For the list of possible sideloads seeWebhook events. | 
metadata | object | {} | Client data. | 
config | object |  | Configuration of the hook. | 
test | object | {} | Input saved for hook testing purposes, seeTest a hook | 
description | string |  | Hook description text. | 
extension_source | string | rossum_store | Import source of the extension. For more, seeExtension sources. | 
settings | object | {} | Specific settings that will be included in the payload when executing the hook. | 
settings_schema | object | null | JSON schema for settings field, specifying the JSON structure of this field. (seeHook settings schema) | 
secrets_schema | object | null | JSON schema for secrets field, specifying the JSON structure of this field. (seeHook secrets schema) | 
guide | string |  | Description how to use the extension. | 
read_more_url | URL |  | URL address leading to more info page. | 
extension_image_url | URL |  | URL address of extension picture. | 
settings_description | list[object] | [] | Contains description for settings | 
store_description | string |  | Description of hook displayed in Rossum store. | 
external_url | string |  | External URL to be called (relates towebhooktype). | 
use_token_owner | boolean | false | Whether the hook should use token owner. | 
install_action | string | copy | Whether the hook is added directly via application (copy) or on customer's request (request_access). | 
token_lifetime_s | integer | null | Lifetime number of seconds forrossum_authorization_token(min=0, max=7200). This setting will ensure the token will be valid after hook response is returned. Ifnull, default lifetime of600is used. | 
order | integer | 0 | Hook templates can be ordered or grouped by this parameter. | 


#### Settings description object


Attribute | Type | Default | Description
--- | --- | --- | ---
name | string |  | Name of settings attribute
description | string |  | Description of settings attribute
tooltip | string |  | Tooltip for the attribute


#### Hook template variables

You can use variable substitution in Hook Templates. To use it, surround an available variable like
so{{magic_variable}}anywhere in the request body. If the variable is available, it will be replaced.
If the variable is not available, response will return500.

Variable
---
api_url
webhook_base_domain
webhook_domain_prefix


### List all hook templates

> List all hook templates
List all hook templates

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hook_templates'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/hook_templates/1","metadata":{},"events":["annotation_status.changed"],"test":{...},"settings":{...},"settings_description":[...],"settings_schema":null,"secrets_schema":null,"name":"Document sorting","type":"function","config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};"},"sideload":["queues"],"description":"Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.","extension_source":"rossum_store","store_description":"<p>Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.</p>","external_url":"","use_token_owner":true,"install_action":"copy","token_lifetime_s":null,"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg"}]}
```

GET /v1/hook_templates
Retrieve all hook template objects.
Supported ordering:order

#### Response

Returnspaginatedresponse with a list ofhook templatesobjects.

### Retrieve a hook template

> Get hook template object1
Get hook template object1

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/hook_templates/1'
```


```
{"url":"https://<example>.rossum.app/api/v1/hook_templates/1","metadata":{},"events":["annotation_status.changed"],"test":{...},"settings":{...},"settings_description":[...],"settings_schema":null,"secrets_schema":null,"name":"Document sorting","type":"function","config":{"runtime":"nodejs22.x","code":"exports.rossum_hook_request_handler = () => {\nconst messages = [{\"type\":\"info\",\"content\":\"Yup!\"}];\nconst operations = [];\nreturn {\nmessages,\noperations\n};\n};"},"sideload":["queues"],"description":"Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.","extension_source":"rossum_store","store_description":"<p>Automatically sort documents into specific queues based on document type (i.e. invoice, bill, PO etc.), POs, vendor, total amount, due date, product or locale.</p>","external_url":"","use_token_owner":true,"install_action":"copy","token_lifetime_s":null,"guide":"Here we explain how the extension should be used.","read_more_url":"https://github.com/rossumai/simple-vendor-matching-webhook-python","extension_image_url":"https://rossum.ai/wp-content/themes/rossum/static/img/logo.svg"}
```

GET /v1/hook_templates/{id}
Get a hook template object.

#### Response

Returnshook templateobject.

## Inbox

> Example inbox object

```
{"id":1234,"name":"Receipts","url":"https://<example>.rossum.app/api/v1/inboxes/1234","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"email":"east-west-trading-co-a34f3a@<example>.rossum.app","email_prefix":"east-west-trading-co","bounce_email_to":"bounces@east-west.com","bounce_unprocessable_attachments":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":true,"metadata":{},"filters":{"allowed_senders":["*@rossum.ai","john.doe@company.com","john.doe@company.??"],"denied_senders":["spam@*"],"document_rejection_conditions":{"enabled":true,"resolution_lower_than_px":[1200,600],"file_size_less_than_b":null,"mime_types":["image/gif"],"file_name_regexes":null}},"dmarc_check_action":"accept","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z"}
```

An inbox object enables email ingestion to a relatedqueue. We
enforceemaildomain to match Rossum domain (e.g..rossum.app).email_prefixmay be used to construct unique email address.
Please note that due to security reasons, emails from Rossum do not contain processed files.
This feature can be enabled upon request by customer support.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the inbox | true
name | string |  | Name of the inbox (not visible in UI) | 
url | URL |  | URL of the inbox | true
queues | list[URL] |  | Queue that receives documents from inbox. Queue has to be passed in list due to backward compatibility. It is possible to have only one queue per inbox. | 
email | EMAIL |  | Rossum email address (e.g.east-west-trading-co-a34f3a@<example>.rossum.app) | 
email_prefix | string |  | Rossum email address prefix (e.g.east-west-trading-co). Maximum length allowed is 57 chars. | 
bounce_email_to | EMAIL |  | (Deprecated) Email address to send notifications to (e.g. about failed import). Configuration moved toEmail notifications settings. | 
bounce_unprocessable_attachments | bool | false | (Deprecated) Whether return back unprocessable attachments (e.g. MS Word docx) or just silently ignore them. When true,minimum image sizerequirement does not apply. Configuration moved toEmail notifications settings. | 
bounce_postponed_annotations | bool | false | (Deprecated) Whether to send notification when annotation is postponed. Configuration moved toEmail notifications settings. | 
bounce_deleted_annotations | bool | false | (Deprecated) Whether to send notification when annotation is deleted. Configuration moved toEmail notifications settings. | 
bounce_email_with_no_attachments | bool | true | (Deprecated) Whether to send notification when no processable documents were found. Configuration moved toEmail notifications settings. | 
metadata | object | {} | Client data. | 
filters | object | {} | Filtering of incoming emails and documents, seefilters | 
dmarc_check_action | string | accept | Decides what to do with incoming emails, that don't pass the DMARC check. Available values areacceptanddrop. | 
modified_by | URL | null | Last modifier. | true
modified_at | datetime | null | Time of last modification. | true


#### Filters attribute

allowed_sendersanddenied_senderssettings allow filtering of incoming emails based on sender email address. Filters can be specified by exact
email addresses as well as using expressions containing wildcards:
- *matches everything (e.g.*@rossum.aimatches every email fromrossum.aidomain)
- ?matches any single character (e.g.john?doe@rossum.aimatchesjohn.doe@rossum.aias well asjohn-doe@rossum.ai)
document_rejection_conditionsdefines rules for filtering incoming documents via email.

Attribute | Type | Default | Description
--- | --- | --- | ---
allowed_senders | list[string] | [] | Only emails with matching sender's address will be processed. If empty all senders all allowed.
denied_senders | list[string] | [] | Incoming emails from email address matching one of these will be ignored.
document_rejection_conditions | object | {} | Rules for filtering out documents coming to Rossum smart inbox. Seedocument rejection conditions object


#### Document rejection conditions object

This object configures filtering of documents Rossum received via its smart inbox. If it's enabled document will be rejected
once it satisfied at least one of defined conditions.
Setting attribute value to null (or empty list in case ofmime_types,file_name_regexes) will turn that specific filtering feature off.

Attribute | Type | Default | Description
--- | --- | --- | ---
enabled | bool | true | Whether the document rejection feature is enabled.
resolution_lower_than_px | tuple[integer, integer] | [1200, 600] | Resolution [width, height] in pixels. A file will be filtered out if both of the dimensions are smaller than the limits.
file_size_less_than_b | integer | null | Size of document in bytes. A file with smaller size will be filtered out.
mime_types | list[string] | ["image/gif"] | List of mime types to filter out (must match^.+/.+$).
file_name_regexes | list[string] | null | Regular expressions inre2format (for more info about syntax seedocs). A file with matching name will be filtered out.


### List all inboxes

> List all inboxes

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/inboxes'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":1234,"name":"Receipts","url":"https://<example>.rossum.app/api/v1/inboxes/1234","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"email":"east-west-trading-co-recepits@<example>.rossum.app","email_prefix":"east-west-trading-co-recepits","bounce_email_to":"bounces@east-west.com","bounce_unprocessable_attachments":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":true,"metadata":{},"filters":{"allowed_senders":[],"denied_senders":[]},"dmarc_check_action":"accept","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z"},{"id":1244,"name":"Beta Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-beta@<example>.rossum.app","email_prefix":"east-west-trading-co-beta","bounce_email_to":"bill@east-west.com","bounce_unprocessable_attachments":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":false,"metadata":{},"filters":{"allowed_senders":["*@east-west.com"],"denied_senders":[]},"dmarc_check_action":"accept""modified_by":null,"modified_at":null}]}
```

Retrieve all inbox objects.
Supported filters:id,name,email,email_prefix,bounce_email_to,bounce_unprocessable_attachments,bounce_postponed_annotations,bounce_deleted_annotations
Supported ordering:id,name,email,email_prefix,bounce_email_to
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofinboxobjects.

### Create a new inbox

> Create new inbox related to queue8236namedTest Inbox
Create new inbox related to queue8236namedTest Inbox

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Inbox", "email_prefix": "east-west-trading-co-test", "bounce_email_to": "joe@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"], "filters": {"allowed_senders": ["*@east-west-trading.com"]}}'\'https://<example>.rossum.app/api/v1/inboxes'
```


```
{"id":1244,"name":"Test Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-test-b21e3a@<example>.rossum.app","email_prefix":"east-west-trading-co-test","bounce_email_to":"joe@east-west-trading.com","bounce_unprocessable_attachments":false,"bounce_postponed_annotations":false,"bounce_deleted_annotations":false,"bounce_email_with_no_attachments":true,"metadata":{},"filters":{"allowed_senders":["*@east-west-trading.com"],"denied_senders":[]},"dmarc_check_action":"accept","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z"}
```

Create a new inbox object.

#### Response

Returns createdinboxobject.

### Retrieve an inbox

> Get inbox object1244

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/inboxes/1244'
```


```
{"id":1244,"name":"Test Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-beta@<example>.rossum.app",...}
```


#### Response


### Update an inbox

> Update inbox object1244
Update inbox object1244

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Shiny Inbox", "email": "east-west-trading-co-test@<example>.rossum.app", "bounce_email_to": "jack@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"]}'\'https://<example>.rossum.app/api/v1/inboxes/1244'
```


```
{"id":1244,"name":"Shiny Inbox","url":"https://<example>.rossum.app/api/v1/inboxes/1244","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"email":"east-west-trading-co-test@<example>.rossum.app","bounce_email_to":"jack@east-west-trading.com",...}
```


#### Response

Returns updatedinboxobject.

### Update a part of an inbox

> Update email of inbox object1244
Update email of inbox object1244

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Common Inbox"}'\'https://<example>.rossum.app/api/v1/inboxes/1244'
```


```
{"id":1244,"name":"Common Inbox",...}
```

PATCH /v1/inboxes/{id}
Update a part of inbox object.

#### Response

Returns updatedinboxobject.

### Delete an inbox

> Delete inbox1244

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/inboxes/1244'
```

DELETE /v1/inboxes/{id}

#### Response


## Label

> Example label object

```
{"id":1,"url":"https://<example>.rossum.app/api/v1/labels/1","name":"expedite","organization":"https://<example>.rossum.app/api/v1/organizationss/1","color":"#FF5733",}
```

Label object represents arbitrary labels added toannotationobjects.

Attribute | Type | Read-only | Default | Description
--- | --- | --- | --- | ---
id | integer | yes |  | Label object ID.
url | URL | yes |  | Label object URL.
name | string | no |  | Text of the label.
organization | URL | yes |  | Organization the label belongs to.
color | string | no | null | Color of the label in RGB hex format.


### List all labels

> List all labels

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/labels'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/labels/1",...}]}
```

List all label objects.
Supported filters:id,name
Supported ordering:id,name
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list oflabelobjects.

### Retrieve label

> Get label object123

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/labels/123'
```


```
{"id":123,"url":"https://<example>.rossum.app/api/v1/labels/123",...}
```

Retrieve a label object.

#### Response


### Create a new label

> Create new label

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "expedite"}'\'https://<example>.rossum.app/api/v1/labels'
```


```
{"id":42,"url":"https://<example>.rossum.app/api/v1/labels/42",...}
```

Create a new label object.

#### Response

Returns createdlabelobject.

### Update part of a label

> Update content of label object42
Update content of label object42

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Unreadable"}'\'https://<example>.rossum.app/api/v1/labels/42'
```


```
{"id":42,"url":"https://<example>.rossum.app/api/v1/labels/42",...}
```

PATCH /v1/labels/{id}
Update part of label object.

#### Response

Returns updatedlabelobject.

### Update a label

> Update label object42
Update label object42

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "postpone"}'\'https://<example>.rossum.app/api/v1/labels/42'
```


```
{"id":42,"url":"https://<example>.rossum.app/api/v1/labels/42",...}
```


#### Response

Returns updatedlabelobject.

### Delete a label

> Delete label42

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/labels/42'
```

DELETE /v1/labels/{id}

#### Response


### Add/Remove labels on annotations

> Add label42, remove label43to annotations10,11
Add label42, remove label43to annotations10,11

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"operations": {"add": ["https://<example>.rossum.app/api/v1/labels/42"], \
                      "remove": ["https://<example>.rossum.app/api/v1/labels/43"]}, \
  "objects": {"annotations": ["https://<example>.rossum.app/api/v1/annotations/10", \
                              "https://<example>.rossum.app/api/v1/annotations/11"]}}'\'https://<example>.rossum.app/api/v1/labels/apply'
```

POST /v1/labels/apply
Add/Remove labels on annotations.

#### Response


## Membership

> Example membership object
Example membership object

```
{"id":3,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/3","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/4","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/3","https://<example>.rossum.app/api/v1/organization_groups/1/queues/4"],"expires_at":null}
```

Membership represents a relation between user, organization (besides its primary organization) and queues.
It provides a way how users can work with multiple organizations within the same organization group. Using
memberships one can query the resources from a different organization the same way how one would do in
their own organization. To do so, a membership shall becreatedfirst, then
a membership token shall begenerated. Such token then
can be used in any subsequent calls made to the target organization.

Attribute | Type | Default | Description
--- | --- | --- | ---
id | integer |  | Id of the membership
url | URL |  | URL of the membership
user | URL |  | URL of the user
organization | URL |  | URL of the organization
queues | list[URL] |  | URLs of queues user has access to
expires_at | datetime | null | Timestamp of membership expiration. Membership won't expire if no expiration is set.


### List all memberships

> List all memberships in organization group1
List all memberships in organization group1

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/1/memberships'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":3,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/3","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/4","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/1","https://<example>.rossum.app/api/v1/organization_groups/1/queues/2"],"expires_at":null},{"id":4,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/4","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/5","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/1"],"expires_at":null}]}
```

GET /v1/organization_groups/{id}/memberships
Retrieve all membership objects.
Supported filters:user,organization
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofmembershipobjects.

### Retrieve a membership

> Get membership object with ID4in organization group1
Get membership object with ID4in organization group1

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/1/memberships/4'
```


```
{"id":4,"url":"https://<example>.rossum.app/api/v1/organization_groups/1/memberships/4","user":"https://<example>.rossum.app/api/v1/organization_groups/1/users/5","organization":"https://<example>.rossum.app/api/v1/organization_groups/1/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/1/queues/1"],"expires_at":null}
```

GET /v1/organization_groups/{id}/memberships/{id}
Get a membership object.

#### Response

Returnsmembershipobject.

### Create new membership

> Create new membership
Create new membership

```
curl-s-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{ \
        "user": "https://<example>.rossum.app/api/v1/organization_groups/2/users/6", \
        "organization": "https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5", \
        "queues": ["https://<example>.rossum.app/api/v1/organization_groups/2/queues/6"]
        }''https://<example>.rossum.app/api/v1/organization_groups/2/memberships'
```


```
{"id":5,"url":"https://<example>.rossum.app/api/v1/organization_groups/2/memberships/5","user":"https://<example>.rossum.app/api/v1/organization_groups/2/users/6","organization":"https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5","queues":[],"expires_at":null}
```

POST /v1/organization_groups/{id}/memberships
Create a membership object.

#### Response

Returnsmembershipobject.

### Partially update membership

> Partially update membership with ID7in organization group2
Partially update membership with ID7in organization group2

```
curl-s-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"queues": ["https://<example>.rossum.app/api/v1/organization_groups/2/queues/6"]}'\'https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7'
```


```
{"id":7,"url":"https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7","user":"https://<example>.rossum.app/api/v1/organization_groups/2/users/6","organization":"https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/2/queues/6"],"expires_at":null}
```

PATCH /v1/organization_groups/{id}/memberships/{id}
Update a part of membership object.

#### Response

Returnsmembershipobject.

### Update membership

> Update membership with ID7in organization group2
Update membership with ID7in organization group2

```
curl-s-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{ \
    "user": "https://<example>.rossum.app/api/v1/organization_groups/2/users/7", \
    "organization": "https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5", \
    "queues": ["https://<example>.rossum.app/api/v1/organization_groups/2/queues/12"]
    }''https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7'
```


```
{"id":7,"url":"https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7","user":"https://<example>.rossum.app/api/v1/organization_groups/2/users/7","organization":"https://<example>.rossum.app/api/v1/organization_groups/2/organizations/5","queues":["https://<example>.rossum.app/api/v1/organization_groups/2/queues/12"],"expires_at":null}
```

PUT /v1/organization_groups/{id}/memberships/{id}
Update a membership object.

#### Response

Returnsmembershipobject.

### Delete membership

> Delete membership with ID7in organization group2
Delete membership with ID7in organization group2

```
curl-s-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/2/memberships/7'
```

DELETE /v1/organization_groups/{id}/memberships/{id}
Delete a membership object.

#### Response


## Note

> Example note object

```
{"id":1,"url":"https://<example>.rossum.app/api/v1/notes/1","type":"rejection","metadata":{},"content":"Arbitrary note text","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T10:08:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/1"}
```

Note object represents arbitrary notes added toannotationobjects.

Attribute | Type | Read-only | Description
--- | --- | --- | ---
id | integer | yes | Note object ID.
url | URL | yes | Note object URL.
metadata | object | no | Client data.
content | string (max. 4096 chars) | no | Note's string content.
created_at | datetime | yes | Timestamp of object's creation.
creator | URL | yes | User that created the note.
modified_at | datetime | yes | Timestamp of last modification.
modifier | URL | yes | User that last modified the note.
modified_by | URL | yes | User that last modified the note.
annotation | URL | no | Annotation the note belongs to.
type | string | no | Note type. Possible values:rejection.


### List all notes

> List all notes

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/notes'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/notes/1","type":"rejection","metadata":{},"content":"Arbitrary note text","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T10:08:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/1"}]}
```

List all note objects.
Supported filters:annotation,creator
Supported ordering:modified_at,created_at
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofnoteobjects.

### Retrieve note

> Get note object123

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/notes/123'
```


```
{"id":123,"url":"https://<example>.rossum.app/api/v1/notes/123","type":"rejection","metadata":{},"content":"Arbitrary note text","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T10:08:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/12","modified_by":"https://<example>.rossum.app/api/v1/users/12","annotation":"https://<example>.rossum.app/api/v1/annotations/150"}
```

Retrieve a note object.

#### Response


### Create a new note

> Create new note related to annotation45
Create new note related to annotation45

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": "Does not have invoice ID", "type": "rejection", "annotation": "https://<example>.rossum.app/api/v1/annotations/45"}'\'https://<example>.rossum.app/api/v1/notes'
```


```
{"id":42,"url":"https://<example>.rossum.app/api/v1/notes/42","type":"rejection","metadata":{},"content":"Does not have invoice ID","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":null,"modifier":null,"modified_by":null,"annotation":"https://<example>.rossum.app/api/v1/annotations/45"}
```

Create a new note object.

#### Response

Returns creatednoteobject.

### Update part of a note

> Update content of note object42
Update content of note object42

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content": "Unreadable"}'\'https://<example>.rossum.app/api/v1/notes/42'
```


```
{"id":42,"url":"https://<example>.rossum.app/api/v1/notes/42","type":"rejection","metadata":{},"content":"Unreadable","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T011:10:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/45"}
```

Update part of note object.

#### Response

Returns updatednoteobject.

### Update a note

> Update note object42

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "rejection", "content": "Misspelled vendor ID", "annotation": "https://<example>.rossum.app/api/v1/annotations/45"}'\'https://<example>.rossum.app/api/v1/notes/42'
```


```
{"id":42,"url":"https://<example>.rossum.app/api/v1/notes/42","type":"rejection","metadata":{},"content":"Misspelled vendor ID","created_at":"2021-04-26T009:41:03.543210Z","creator":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2021-04-26T011:10:03.856648Z","modifier":"https://<example>.rossum.app/api/v1/users/1","modified_by":"https://<example>.rossum.app/api/v1/users/1","annotation":"https://<example>.rossum.app/api/v1/annotations/45"}
```


#### Response

Returns updatednoteobject.

### Delete a note

> Delete note42

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/notes/42'
```

DELETE /v1/notes/{id}

#### Response


## Organization

> Example organization object
Example organization object

```
{"id":406,"url":"https://<example>.rossum.app/api/v1/organizations/406","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/7540"],"users":["https://<example>.rossum.app/api/v1/users/10775"],"organization_group":"https://<example>.rossum.app/api/v1/organization_groups/17","ui_settings":{},"metadata":{},"created_at":"2019-09-02T14:28:11.000000Z","trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"oidc_provider":null,"internal_info":{"cs_account_classification":null,"customer_type":null,"market_category":null,"overdue_payment_date":null,"sso_active":false},"creator":"https://<example>.rossum.app/api/v1/users/10775","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

Organization is a basic unit that contains all objects that are required to fully use Rossum platform.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the organization | true
name | string |  | Name of the organization (not visible in UI) | 
url | URL |  | URL of the organization | true
workspaces | list[URL] |  | List of workspaces objects in the organization | true
users | list[URL] |  | List of users in the organization | true
organization_group | URL |  | URL to organization group the organization belongs to | true
ui_settings | object | {} | Organization-wide frontend UI settings (e.g. locales). Rossum internal. | 
metadata | object | {} | Client data. | 
is_trial | bool |  | Property indicates whether this license is a trial license | true
created_at | timestamp |  | Timestamp for when the organization was created | true
trial_expires_at | timestamp |  | Timestamp for when the trial period ended (ISO 8601) | true
oidc_provider | string | null | (Deprecated) OpenID Connect provider name | true
internal_info | object | null | INTERNALRossum internal information on organization. | true
creator | URL | null | URL of the first user of the organization (set during organization creation) | true
modified_by | URL | null | URL of the last modifier | true
modified_at | datetime | null | Date of the last modification | true
settings | object | {} | Settings of the organization (seeorganization settings) | false
sandbox | bool | False | Specifies if the organization is a sandbox | false


#### Organization settings


Attribute | Type | Description | Default
--- | --- | --- | ---
annotation_list_table | object | Configuration of annotation dashboard columns | {}


### Create new organization


```
curl-s-XPOST-H'Content-Type: application/json'\-d'{"template_name": "UK Demo Template", "organization_name": "East West Trading Co", "user_fullname": "John Doe", "user_email": "john@east-west-trading.com", "user_password": "owo1aiG9ua9Aihai", "user_ui_settings": { "locale": "en" }, "create_key": "13156106d6f185df24648ac7ff20f64f1c5c06c144927be217189e26f8262c4a", "domain": "acme-corp"}'\'https://<example>.rossum.app/api/v1/organizations/create'
```


```
{"organization":{"id":105,"url":"https://<example>.rossum.app/api/v1/organizations/105","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/160"],"users":["https://<example>.rossum.app/api/v1/users/173"],"organization_group":"https://<example>.rossum.app/api/v1/organization_groups/17","ui_settings":{},"metadata":{},"trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"oidc_provider":null,"domain":"acme-corp","phone_number":"721722723","communication_opt_in":false,"creator":"https://<example>.rossum.app/api/v1/users/173"}}
```

POST /v1/organizations/create
Create new organization and related objects (workspace, queue, user, schema, inbox, domain).

Attribute | Type | Default | Description | Required
--- | --- | --- | --- | ---
template_name | enum |  | Template to use for new organization (see below) | true
organization_name | string |  | Name of the organization. Will be also used as a base for inbox e-mail address. | true
user_fullname | string |  | Full user name | true
user_email | EMAIL |  | Valid email of the user (also used as Rossum login) | true
user_password | string | *generated | Initial user password | 
user_ui_settings | object | {"locale": "en"} | Initial UI settings | 
create_key | string |  | A key that allows to create an organization | true
 |  |  |  | 

You need acreate_keyin order to create an organization. Please contactsupport@rossum.aito obtain one.
Selectedtemplate_nameaffects default schema and extracted fields. Please
note that the demo templates may be updated as new features are introduced.

Template name | Description | Is demo
--- | --- | ---
Empty Organization Template | Empty organization, suitable for further customization | no
CZ Demo Template | Czech standard invoices | yes
Tax Invoice EU Demo Template | VAT Invoices, Credit Notes, Debit Notes, Purchase/Sales Orders, Receipts, and Pro Formas coming from the EU | yes
Tax Invoice US Demo Template | Tax Invoices, Credit Notes, Debit Notes, Purchase/Sales Orders, Receipts, and Pro Formas coming from the US | yes
Tax Invoice UK Demo Template | VAT Invoices, Credit Notes, Debit Notes, Purchase/Sales Orders, Receipts, and Pro Formas coming from the UK, India, Canada, or Australia | yes
Delivery Note Demo Template | Delivery Notes | yes
Tax Invoice CN Demo Template | governmental Tax Invoices from Mainland China (fapiaos) | yes
Certificates of Analysis Demo Template | Certificates of Analysis that are quality control documents common in the food and beverage industry | yes


#### Response

Returns object withorganizationkey andorganizationobject value.

### Organization limits

Used to get information about various limits in regard to Organization.
> Get Organization limits.
Get Organization limits.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/5/limits'
```


```
{"email_limits":{"count_today":7,"count_today_notification":4,"count_total":9,"email_per_day_limit":10,"email_per_day_limit_notification":10,"email_total_limit":20,"last_sent_at":"2022-01-13","last_sent_at_notification":"2022-01-13"}}
```

GET /v1/organizations/{id}/limits

#### Response

The response currently consists only ofemail_limits.

Attribute | Type | Description
--- | --- | ---
count_today | integer | Emails sent by user today count.
count_today_notification | integer | Notification emails sent today count.
count_total | integer | Emails sent by user total count.
email_per_day_limit | integer | Emails sent by user today limit.
email_per_day_limit_notification | integer | Notification emails sent today limit.
email_total_limit | integer | Emails sent by user total limit.
last_sent_at | date | Date of last sent email.
last_sent_at_notification | date | Date of last sent notification.


### List all organizations

> List all organizations
List all organizations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":406,"url":"https://<example>.rossum.app/api/v1/organizations/406","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/7540"],"users":["https://<example>.rossum.app/api/v1/users/10775"],"organization_group":"https://<example>.rossum.app/api/v1/organization_groups/17","ui_settings":{},"metadata":{},"created_at":"2019-09-02T14:28:11.000000Z","trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"internal_info":{"cs_account_classification":null,"customer_type":null,"market_category":null,"overdue_payment_date":null},"creator":"https://<example>.rossum.app/api/v1/users/10775","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
```

GET /v1/organizations
Retrieve all organization objects.
Supported filters:id,name
Supported ordering:id,name
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list oforganizationobjects. Usually, there would only be one organization.

### Retrieve an organization

> Get organization object406
Get organization object406

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations/406'
```


```
{"id":406,"url":"https://<example>.rossum.app/api/v1/organizations/406","name":"East West Trading Co","workspaces":["https://<example>.rossum.app/api/v1/workspaces/7540"],"users":["https://<example>.rossum.app/api/v1/users/10775"],"ui_settings":{},"metadata":{},"created_at":"2019-09-02T14:28:11.000000Z","trial_expires_at":"2020-09-02T14:28:11.000000Z","is_trial":true,"internal_info":{"cs_account_classification":null,"customer_type":null,"market_category":null,"overdue_payment_date":null},"creator":"https://<example>.rossum.app/api/v1/users/10775","modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

GET /v1/organizations/{id}
Get an organization object.

#### Response

Returnsorganizationobject.

### Generate a token to access the organization

> Generate a token for organization 406
Generate a token for organization 406

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/auth/membership_token'-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406"}'
```


```
{"key":"b6dde6e6280c697bc4afac7f920c5cee8c9c9t7d","organization":"https://<example>.rossum.app/api/v1/organizations/406"}
```

POST /v1/auth/membership_token
Generate token for access to membership and primary organizations. If the user is a group administrator, token can be generated for any organization in his organization group.

Attribute | Type | Description | Required
--- | --- | --- | ---
organization | URL | URL to theorganizationto which the token will have access | Yes
origin | string | For internal use only. Using this field may affectthrottlingof your API requests. | No


#### Response

Returns object withkey(authorization token belonging to requested organization) andorganizationURL.

### Retrieve all membership organizations

> Get organizations the user is a member of
Get organizations the user is a member of

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organizations?include_membership_organizations=true'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":741924,"url":"https://<example>.rossum.app/api/v1/organizations/741924","name":"Best organization",...},...]}
```

GET /v1/organizations?include_membership_organizations=true
Returnspaginatedresponse with a list of organizations that user is either in or is connected to through membership. If user isorganization group admin, he can list all the organizations from the organization group.

#### Response

Returns list oforganizationobjects.

### Billing for organization


#### Billing stats for organization

In order to obtain an overview of the billed items, you can get basic billing statistics.
> Download billing stats report (August 1, 2021 - August 31, 2021).
Download billing stats report (August 1, 2021 - August 31, 2021).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-08-01", "end_date": "2021-08-31", "queues": [
      "https://<example>.rossum.app/api/v1/queues/8199"]}, "group_by": ["queue"]}'\'https://<example>.rossum.app/api/v1/organizations/789/billing_stats'
```

POST /v1/organizations/{id}/billing_stats

Attribute | Type | Description
--- | --- | ---
filters | object | Filters used for the computation of billed items counts (seebilling stats filters)
group_by | list[string] | List of attributes by which theresultsare to be grouped. Only a single value is supported. Possible values:queue,monthandweek.
order_by | list[string] | List of attributes by which theresultsare to be ordered. Possible values:billable_pages,billable_documents,non_billable_pages,non_billable_pages


Attribute | Type | Description
--- | --- | ---
queues | list[URL] | Filter billed items for the specified queues (ornullfor historically deleted queues) to be counted to the report
begin_date | datetime | Filter billed items that was issuedsincethe specified date (including the specified date) to be counted to the report.
end_date | datetime | Filter billed items that was issuedup tothe specified date (including the specified date) to be counted to the report.


```
{"pagination":{"next":null,"previous":null,"total":11,"total_pages":1},"results":[{"begin_date":"2021-10-01","end_date":"2021-10-31","organization":"https://<example>.rossum.app/api/v1/organizations/406","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"billable_documents":13,"billable_pages":7,"non_billable_documents":0,"non_billable_pages":0}},{"begin_date":"2021-12-01","end_date":"2021-12-31","organization":"https://<example>.rossum.app/api/v1/organizations/406","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"billable_documents":5,"billable_pages":5,"non_billable_documents":0,"non_billable_pages":0}},...],"totals":{"billable_documents":21288,"billable_pages":30204,"non_billable_documents":81,"non_billable_pages":5649},"updated_at":"2022-09-01"}
```

paginatedresponse with a list ofbilling stats resultsobjects and atotalsobject.
Totalscontain summary information for the whole period (betweenbegin_dateandend_date). The contract defines
the billing unit (pagesordocuments).

Attribute | Type | Description
--- | --- | ---
billable_documents | int | Number of documents billed.
billable_pages | int | Number of pages billed.
non_billable_documents | int | Number of documents that were received but not billed.
non_billable_pages | int | Number of pages that were received but not billed.

Resultscontain information grouped by fields defined ingroup_by. The data (seeabove)
are wrapped invaluesobject, and accompanied by the values of attributes that were used for grouping.

Attribute | Type | Description
--- | --- | ---
queue | URL | Billed pages or documents Queue
organization | URL | Billed pages or documents Organization
begin_date | date | Start date of the pages or documents billing info within the group
end_date | date | Final date of the pages or documents billing info within the group
values | object | Contains the data oftotalslist grouped by thegroup_by.


#### Billing history for organization

> Retrieve billing history report.
Retrieve billing history report.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organizations/42/billing_history'
```

GET /v1/organizations/{id}/billing_history
Retrieve billing history with entries corresponding to individual contracted periods. The valuepuchased_documentsorpurchased_pagesdefine the period billing unit.

```
{"pagination":{"next":null,"previous":null,"total":2,"total_pages":1},"results":[{"begin_date":"2021-01-01","end_date":"2022-12-31","values":{"billable_documents":0,"non_billable_documents":0,"billable_pages":34735,"non_billable_pages":20,"is_current":true,"purchased_documents":0,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}},{"begin_date":"2020-01-01","end_date":"2021-12-31","values":{"billable_documents":10209,"non_billable_documents":20,"billable_pages":0,"non_billable_pages":0,"is_current":false,"purchased_documents":111,"purchased_pages":0,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}}],"totals":{"billable_documents":10209,"non_billable_documents":20,"billable_pages":34735,"non_billable_pages":20,"purchased_documents":111,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0},"updated_at":"2022-09-01"}
```


#### Billing stats export for organization

> Download billing stats CSV report (Sep 1, 2021 - August 31, 2022).
Download billing stats CSV report (Sep 1, 2021 - August 31, 2022).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-10-01", "end_date": "2022-09-31"}, "group_by": ["month"]}'\'https://<example>.rossum.app/api/v1/organizations/406/billing_stats/export'
```

POST /v1/organizations/{id}/billing_stats/export
Download the data provided by thebilling stats response resourcein a CSV output.

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


#### Billing history export for organization

> Download billing history CSV report.
Download billing history CSV report.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organizations/406/billing_history/export'
```

GET /v1/organizations/{id}/billing_history/export
Download the data provided by thebilling history response resourcein a CSV output.

#### Response


```
begin_date,end_date,purchased_pages,billable_pages,non_billable_pages,purchased_documents,billable_documents,non_billable_documents,extracted_pages_with_learning,extracted_pages_without_learning,split_pages_with_learning,split_pages_without_learning,extracted_documents_with_learning,extracted_documents_without_learning,split_documents_with_learning,split_documents_without_learning,ocr_only_pages,ocr_only_documents,purchased_extracted_pages_with_learning,purchased_extracted_pages_without_learning,purchased_split_pages_with_learning,purchased_split_pages_without_learning,purchased_extracted_documents_with_learning,purchased_extracted_documents_without_learning,purchased_split_documents_with_learning,purchased_split_documents_without_learning,purchased_ocr_only_pages,purchased_ocr_only_documents
2021-01-01,2022-12-31,555,34735,100,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2020-01-01,2021-12-31,0,0,0,111,10209,123,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
```


#### Billing for organization

In order to obtain an overview of the billed items, you can get basic billing statistics.
> Download billing report (August 1, 2021 - August 31, 2021).
Download billing report (August 1, 2021 - August 31, 2021).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filter": {"begin_date": "2021-08-01", "end_date": "2021-08-31", "queues": [
      "https://<example>.rossum.app/api/v1/queues/8199"]}, "group_by": ["queue"]}'\'https://<example>.rossum.app/api/v1/organizations/789/billing'
```

POST /v1/organizations/{id}/billing

Attribute | Type | Description
--- | --- | ---
filter | object | Filters used for the computation of billed items counts
filter.queues | list[URL] | Filter billed items for the specified queues to be counted to the report
filter.begin_date | datetime | Filter billed items that was issuedsincethe specified date (including the specified date) to be counted to the report.
filter.end_date | datetime | Filter billed items that was issuedup tothe specified date (including the specified date) to be counted to the report.
group_by | list[string] | List of attributes by which theseriesis to be grouped. Possible values:queue.


#### Response


```
{"series":[{"begin_date":"2019-02-01","end_date":"2019-02-01","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"header_fields_per_page":2,"header_fields_per_document":5,"header_fields_and_line_items_per_page":9,"header_fields_and_line_items_per_document":20}},{"begin_date":"2019-02-02","end_date":"2019-02-02","queue":"https://<example>.rossum.app/api/v1/queues/8199","values":{"header_fields_per_page":2,"header_fields_per_document":5,"header_fields_and_line_items_per_page":9,"header_fields_and_line_items_per_document":20}},,...],"totals":{"header_fields_per_page":8,"header_fields_per_document":16,"header_fields_and_line_items_per_page":20,"header_fields_and_line_items_per_document":43}}
```

The response consists of two parts:totalsandseries.

#### Billing totals

Totalscontain summary information for the whole period (betweenbegin_dateandend_date).

Attribute | Type | Description
--- | --- | ---
header_fields_per_page | int | Number of pages that were processed by Rossum AI Engine and where only header fields were supposed to be captured.
header_fields_per_document | int | Number of documents that were processed by Rossum AI Engine and where only header fields were supposed to be captured.
header_fields_and_line_items_per_page | int | Number of pages that were processed by Rossum AI Engine and where line item fields were supposed to be captured.
header_fields_and_line_items_per_document | int | Number of documents that were processed by Rossum AI Engine and where line item fields were supposed to be captured.


#### Billing series

Seriescontain information grouped by fields defined ingroup_by. Only grouping byqueueis allowed.
The data (seeabove) are wrapped invaluesobject,
and accompanied by the values of attributes that were used for grouping.

Attribute | Type | Description
--- | --- | ---
queue | URL | Queue of billed pages or documents
begin_date | date | Start date of the documents with billed items within the group
end_date | date | Final date of the documents with billed items within the group
values | object | Contains the data oftotalslist grouped by queue and date.


## Organization group

> Example organization group object
Example organization group object

```
{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu","features":null,"usage":{}}
```

Organization group object represents coupling among organizations.

Attribute | Type | Description | Read-only
--- | --- | --- | ---
id | integer | Id of the organization group | 
name | string | Name of the organization group | 
is_trial | bool | Property indicates whether this license is a trial license | true
is_production | bool | Property indicates whether this licence is a production licence | true
deployment_location | string | Deployment location identifier | true
features | object | Enabled features (for internal use only) | true
usage | object | Enabled priced features (for internal use only) | true
modified_by | URL | URL of the last modifier | true
modified_at | datetime | Date of the last modification | true


### List all organization groups

> List all organization groups.
List all organization groups.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu","features":null,"usage":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}]}
```

GET /v1/organization_groups
Retrieve all organization group objects.

#### Response

Returnspaginatedresponse with a list oforganization groupobjects. Typically, there would only be one result.

### Retrieve an organization group

> Get organization group object42
Get organization group object42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42'
```


```
{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu",...}
```

GET /v1/organization_groups/{id}
Get an organization group object.

#### Response

Returnsorganization groupobject.

### Create a new organization group

> Create a new organization group
Create a new organization group

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organization_groups'
```


```
{"id":42,"name":"Rossum group","is_trial":false,"is_production":true,"deployment_location":"prod-eu",...}
```

POST /v1/organization_groups
Create a neworganization groupobject.

#### Response

Returns the createdorganization groupobject.

### Managing memberships

The following endpoints provide read-only views for users with theorganization_group_adminrole  for managing memberships. The returned object views have a selected subset of their attributes. The URL attributes point to the membership objects instead of the full views.

#### Membership User


Attribute | Type | Description
--- | --- | ---
id | integer | Id of the user
url | URL | Membership URL of the user
email | string | Email of the user
username | string | Username of a user
organization | URL | Relatedorganization


#### Retrieve a User

> Get user123456from organization group42
Get user123456from organization group42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/users/123456'
```


```
{"id":123456,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/users/123456","email":"john-doe@east-west-trading.com","username":"JohnDoe","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321"}
```

GET /v1/organization_groups/{organization_group_id}/users/{user_id}
Get user for an organization group object.
Retrieve a singleorganization groupuser.

#### List all Users in an Organization group

> Get users from organization group42
Get users from organization group42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/users'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":123456,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/users/123456","email":"john-doe@east-west-trading.com","username":"JohnDoe","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321"},{...}]}
```

GET /v1/organization_groups/{id}/users
Get users for an organization group object.
Retrieve allorganization groupusers.

#### Membership Organization


Attribute | Type | Description
--- | --- | ---
id | integer | Id of the organization
url | URL | Membership URL of the organization
name | string | Name of the organization (not visible in UI)


#### Retrieve an Organization

> Get organization321from organization group42
Get organization321from organization group42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321'
```


```
{"id":321,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","name":"East West Trading Co"}
```

GET /v1/organization_groups/{organization_group_id}/organizations/{organization_id}
Get organization for an organization group object.
Retrieve a singleorganization grouporganization.

#### List all Organizations in an Organization group

> Get organizations from organization group42
Get organizations from organization group42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/organizations'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":321,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","name":"East West Trading Co"},{...}]}
```

GET /v1/organization_groups/{id}/organizations
Get organizations for an organization group object.
Retrieve allorganization grouporganizations.

#### Membership workspace


Attribute | Type | Description
--- | --- | ---
id | integer | Id of the workspace
url | URL | Membership URL of the workspace
name | string | Name of the workspace
organization | URL | Membership URL of the organization
queues | list[URL] | Membership URLs of the queues


#### Retrieve a Workspace

> Get workspace345from organization group42
Get workspace345from organization group42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/345'
```


```
{"id":345,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/345","name":"East West Trading Co","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/123","queues":["https://<example>.rossum.app/api/v1/organization_groups/42/queues/1","https://<example>.rossum.app/api/v1/organization_groups/42/queues/2"]}
```

GET /v1/organization_groups/{organization_group_id}/workspaces/{workspace_id}
Get workspace for an organization group object.
Retrieve a singleorganization groupworkspace.

#### List all Workspaces in an Organization group

> Get workspaces from organization group42
Get workspaces from organization group42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/workspaces'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":345,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/345","name":"East West Trading Co","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/123","queues":["https://<example>.rossum.app/api/v1/organization_groups/42/queues/1","https://<example>.rossum.app/api/v1/organization_groups/42/queues/2"]},{...}]}
```

GET /v1/organization_groups/{id}/workspaces
Get workspaces for an organization group object.
Supported filters:organization
For additional info please refer tofilters and ordering.
Retrieve allorganization groupworkspaces.

#### Membership Queue


Attribute | Type | Description
--- | --- | ---
id | integer | Id of the queue
url | URL | Membership URL of the queue
name | string | Name of the queue
organization | URL | Membership URL of theorganization
workspace | URL | Membership URL of the workspace


#### Retrieve a Queue

> Get queue654from organization group42
Get queue654from organization group42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/queues/654'
```


```
{"id":654,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/queues/654","name":"Received invoices","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","workspace":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/12"}
```

GET /v1/organization_groups/{organization_group_id}/queues/{queue_id}
Get queue for an organization group object.
Retrieve a singleorganization groupqueue.

#### List all Queues in an Organization group

> Get queues from organization group42
Get queues from organization group42

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/organization_groups/42/queues'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":654,"url":"https://<example>.rossum.app/api/v1/organization_groups/42/queues/654","name":"Received invoices","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/321","workspace":"https://<example>.rossum.app/api/v1/organization_groups/42/workspaces/12"},{...}]}
```

GET /v1/organization_groups/{id}/queues
Get queues for an organization group object.
Supported filters:organization
For additional info please refer tofilters and ordering.
Retrieve allorganization groupqueues.

### Billing for organization group


#### Billing stats for organization group

> Download billing stats report (Sep 1, 2021 - August 31, 2022).
Download billing stats report (Sep 1, 2021 - August 31, 2022).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-09-01", "end_date": "2022-08-31", "queues": [
      "https://<example>.rossum.app/api/v1/organization_groups/42/queues/8199", null]}, "group_by": ["queue"]}'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_stats'
```

POST /v1/organization_groups/{id}/billing_stats

Attribute | Type | Description
--- | --- | ---
filter | object | Filters used for the computation of billed items counts (seeorganization group billing stats filtersbelow)
group_by | list[string] | List of attributes by which theresultsare to be grouped. Only a single value is supported. Possible values:organization,queue,monthandweek
order_by | list[string] | List of attributes by which theresultsare to be ordered. Possible values:billable_pages,billable_documents,non_billable_pages,non_billable_pages


Attribute | Type | Description
--- | --- | ---
queues | list[URL] | Membership URL of the queues (ornullfor historically deleted queues) to be counted in the report (see the note below)
organizations | list[URL] | Membership URL of the organizations to be counted in the report
begin_date | datetime | Filter billed items that was issuedsincethe specified date (including the specified date) to be counted to the report.
end_date | datetime | Filter billed items that was issuedup tothe specified date (including the specified date) to be counted to the report.

Additionally there are some limitations with regards to the filter.queues and groupings that can be used together:
- filter.queuescan only be used whenfilter.organizationscontains a single organization
- filter.queuescannot be used forgroup_by=organization
filter.queuescan only be used whenfilter.organizationscontains a single organization
filter.queuescannot be used forgroup_by=organization

```
{"pagination":{"next":null,"previous":null,"total":12,"total_pages":1},"results":[{"begin_date":"2021-10-01","end_date":"2021-10-31","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/406","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","queue":"https://<example>.rossum.app/api/v1/organization_groups/42/queues/8199","values":{"billable_documents":32,"billable_pages":27,"non_billable_documents":0,"non_billable_pages":0}},{"begin_date":"2021-10-01","end_date":"2021-10-31","organization":"https://<example>.rossum.app/api/v1/organization_groups/42/organizations/406","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","queue":null,"values":{"billable_documents":147,"billable_pages":59,"non_billable_documents":0,"non_billable_pages":0}},...],"totals":{"billable_documents":21288,"billable_pages":30204,"non_billable_documents":81,"non_billable_pages":5649},"updated_at":"2022-09-01"}
```

For more details seebilling stats for organization.

#### Billing history for organization group

> Retrieve billing history report.
Retrieve billing history report.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_history'
```

GET /v1/organization_groups/{id}/billing_history
Retrieve billing history with entries corresponding to individual contracted periods. The valuepuchased_documentsorpurchased_pagesdefine the period billing unit.

```
{"pagination":{"next":null,"previous":null,"total":2,"total_pages":1},"results":[{"begin_date":"2021-01-01","end_date":"2022-12-31","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","values":{"billable_documents":0,"non_billable_documents":0,"billable_pages":34735,"non_billable_pages":100,"is_current":true,"purchased_documents":0,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}},{"begin_date":"2020-01-01","end_date":"2021-12-31","organization_group":"https://<example>.rossum.app/api/v1/organization_groups/42","values":{"billable_documents":10209,"non_billable_documents":200,"billable_pages":0,"non_billable_pages":0,"is_current":false,"purchased_documents":111,"purchased_pages":0,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0}}],"totals":{"billable_documents":10209,"non_billable_documents":200,"billable_pages":34735,"non_billable_pages":100,"purchased_documents":111,"purchased_pages":555,"extracted_pages_with_learning":0,"extracted_pages_without_learning":0,"split_pages_with_learning":0,"split_pages_without_learning":0,"extracted_documents_with_learning":0,"extracted_documents_without_learning":0,"split_documents_with_learning":0,"split_documents_without_learning":0,"ocr_only_pages":0,"ocr_only_documents":0,"purchased_extracted_pages_with_learning":0,"purchased_extracted_pages_without_learning":0,"purchased_split_pages_with_learning":0,"purchased_split_pages_without_learning":0,"purchased_extracted_documents_with_learning":0,"purchased_extracted_documents_without_learning":0,"purchased_split_documents_with_learning":0,"purchased_split_documents_without_learning":0,"purchased_ocr_only_pages":0,"purchased_ocr_only_documents":0},"updated_at":"2022-09-01"}
```


#### Billing stats export for organization group

> Download billing stats CSV report (Sep 1, 2021 - August 31, 2022).
Download billing stats CSV report (Sep 1, 2021 - August 31, 2022).

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"filters": {"begin_date": "2021-10-01", "end_date": "2022-09-31"}, "group_by": ["month"]}'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_stats/export'
```

POST /v1/organization_groups/{id}/billing_stats/export
Download the data provided by thebilling stats response resourcein a CSV output.

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


#### Billing history export for organization group

> Download billing history CSV report.
Download billing history CSV report.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\'https://<example>.rossum.app/api/v1/organization_groups/42/billing_history/export'
```

GET /v1/organization_groups/{id}/billing_history/export
Download the data provided by thebilling history response resourcein a CSV output.

```
begin_date,end_date,purchased_pages,billable_pages,non_billable_pages,purchased_documents,billable_documents,non_billable_documents,extracted_pages_with_learning,extracted_pages_without_learning,split_pages_with_learning,split_pages_without_learning,extracted_documents_with_learning,extracted_documents_without_learning,split_documents_with_learning,split_documents_without_learning,ocr_only_pages,ocr_only_documents,purchased_extracted_pages_with_learning,purchased_extracted_pages_without_learning,purchased_split_pages_with_learning,purchased_split_pages_without_learning,purchased_extracted_documents_with_learning,purchased_extracted_documents_without_learning,purchased_split_documents_with_learning,purchased_split_documents_without_learning,purchased_ocr_only_pages,purchased_ocr_only_documents
2021-01-01,2022-12-31,555,34735,100,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
2020-01-01,2021-12-31,0,0,0,111,10209,123,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
```


## Page

> Example page object

```
{"id":558598,"annotation":"https://<example>.rossum.app/api/v1/annotations/314528","number":1,"rotation_deg":0,"mime_type":"image/png","s3_name":"4b66305775c029cb0cfa80fd0ebb2da6","url":"https://<example>.rossum.app/api/v1/pages/558598","content":"https://<example>.rossum.app/api/v1/pages/558598/content","metadata":{},"width":1440,"height":668}
```

A page object contains information about one page of the annotation (we render
pages separately for every annotation, but this will change in the future).
Page objects are created automatically during document import and cannot be
created through the API, you need to use queueuploadendpoint. Pages cannot be deleted directly -- they are deleted on parent annotation delete.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the page | true
url | URL |  | URL of the page. | true
annotation | URL |  | Annotation that page belongs to. | 
number | integer |  | Page index, first page has index 1. | 
rotation_deg | integer |  | Page rotation. | 
mime_type | string |  | MIME type of the page (image/png). | true
s3_name | string |  | Internal | true
content | URL |  | Link to the page raw content (e.g. pdf file). | 
metadata | object | {} | Client data. | 
width | integer | null | Page width (for internal purposes only) | true
height | integer | null | Page height (for internal purposes only) | true


### List all pages

> List all pages

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/pages'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":558598,"annotation":"https://<example>.rossum.app/api/v1/annotations/314528","number":1,"rotation_deg":0,"mime_type":"image/png","s3_name":"7eb0dcc0faa8868b55fb425d21cc60dd","url":"https://<example>.rossum.app/api/v1/pages/558598","content":"https://<example>.rossum.app/api/v1/pages/558598/content","metadata":{},"width":null,"height":null}]}
```

Retrieve all page objects.
Supported filters:id,annotation,number
Supported ordering:id,number,s3_name
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofpageobjects.

### Retrieve a page

> Get page object558598
Get page object558598

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/pages/558598'
```


```
{"id":558598,"annotation":"https://<example>.rossum.app/api/v1/annotations/314528","number":1,"rotation_deg":0,"mime_type":"image/png","s3_name":"7eb0dcc0faa8868b55fb425d21cc60dd","url":"https://<example>.rossum.app/api/v1/pages/558598","content":"https://<example>.rossum.app/api/v1/pages/558598/content","metadata":{}}
```


## Question

> Example question object
Example question object

```
{"uuid":"9e87fcf2-f571-4691-8850-77f813d6861a","text":"How satisfied are you?","answer_type":"scale"}
```

A Question object represents a collection of questions related to asurvey.

Attribute | Type | Description
--- | --- | ---
uuid | string | UUID of the question
url | URL | URL of the question
text | string | Text body of the question
answer_type | enum | Determines the shape of the answer. Possible values: seeanswer type


### List all questions

> List all questions

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/questions'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a",...}]}
```

Retrieve all question objects.

#### Response

Returnspaginatedresponse with a list ofquestionobjects.

### Retrieve a question

> Get question object9e87fcf2-f571-4691-8850-77f813d6861a
Get question object9e87fcf2-f571-4691-8850-77f813d6861a

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a'
```


```
{"url":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a",...}
```

GET /v1/questions/{uuid}
Get a question object.

#### Response

Returnsquestionobject.

## Queue

> Example queue object

```
{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","connector":null,"webhooks":[],"hooks":[],"schema":"https://<example>.rossum.app/api/v1/schemas/31336","inbox":"https://<example>.rossum.app/api/v1/inboxes/1229","users":["https://<example>.rossum.app/api/v1/users/10775"],"session_timeout":"01:00:00","rir_url":"https://all.rir.rossum.ai","rir_params":null,"dedicated_engine":null,"generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876","engine":null,"counts":{"importing":0,"split":0,"failed_import":0,"to_review":2,"reviewing":0,"confirmed":0,"exporting":0,"postponed":0,"failed_export":0,"exported":0,"deleted":0,"purged":0,"rejected":0},"default_score_threshold":0.8,"automation_enabled":false,"automation_level":"never","locale":"en_US","metadata":{},"use_confirmed_state":false,"document_lifetime":"01:00:00","delete_after":null,"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z","settings":{"columns":[{"schema_id":"tags"}],"hide_export_button":true,"automation":{"automate_duplicates":true,"automate_suggested_edit":false},"rejection_config":{"enabled":true},"dashboard_customization":{"all_documents":false,"confirmed":true,"deleted":true,"exported":true,"postponed":true,"rejected":true,"to_review":true},"email_notifications":{"recipient":{"email":"john.doe@company.com","name":"John Doe"},"unprocessable_attachments":false,"email_with_no_attachments":true,"postponed_annotations":false,"deleted_annotations":false},"workflows":{"enabled":false}},"workflows":[{"url":"https://<example>.rossum.app/api/v1/workflows/1","priority":2}]}
```

A queue object represents a basic organization unit of annotations. Annotations
are imported to a queue either through a REST APIupload endpointor by sending an email to a relatedinbox. Export is also performed on a
queue usingexportendpoint.
Queue also specifies aschemafor annotations and aconnector.
Annotators and viewers only see queues they are assigned to.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the queue | true
name | string |  | Name of the queue (max. 255 characters) | 
url | URL |  | URL of the queue | true
workspace | URL |  | Workspace in which the queue should be placed (it can be set tonull, but bare in mind that it will make the queue invisible in the Rossum UI and it may cause some unexpected consequences) | 
connector | URL | null | Connector associated with the queue | 
webhooks | list[URL] | [] | (Deprecated) Webhooks associated with the queue (serves as an alias forhooksattribute) | 
hooks | URLlist[URL] | [] | Hooks associated with the queue | 
schema | URL |  | Schema which will be applied to annotations in this queue | 
inbox | URL | null | Inbox for import to this queue | 
users | list[URL] | [] | Users associated with this queue | 
session_timeout | timedelta | 1 hour | Time before annotation will be returned fromrevievingstatus toto_review(timeout is evaluated every 10 minutes) | 
rir_url | URL | null | (Deprecated) Usegeneric_engineordedicated_engineto set AI Core Engine. | 
generic_engine | URL | null | Generic engine used for processing documents uploaded to this queue. Ifgeneric_engineis setdedicated_enginemust benull. If both engines arenull, a default generic one gets set. | 
dedicated_engine | URL | null | Dedicated engine used for processing documents uploaded to this queue. Ifdedicated_engineis setgeneric_enginemust benull. | 
rir_params | string | null | URL parameters to be passed to the AI Core Engine, see below | 
counts | object |  | Count of annotations perstatus | true
default_score_threshold | float [0;1] | 0.8 | Threshold used to automatically validate field content based onAI confidence scores. | 
automation_enabled | bool | false | Toggle for switching automation on/off | 
automation_level | string | never | Set level of automation, seeAutomation level. | 
locale | string | en_GB | Typical originating region of documents processed in this queue specified in the locale format, see below. Ifautooption is chosen, the locale will be detected automatically if the organization group has access to Aurora engine. Otherwise, default option (en_GB) will be used. | 
metadata | object | {} | Client data. | 
use_confirmed_state | bool | false | Affects exporting: whentrue,confirmendpoint transitions annotation toconfirmedstatus instead toexporting. | 
settings | object | {} | Queue UI settings | 
document_lifetime | duration | null | Data retention period -- annotations will be automatically purged this time after their creation. The format of the value is '[DD] [HH:[MM:]]ss[.uuuuuu]', e.g. 90 days retention can be set as '90 00:00:00'. Please keep in mind that purging documents in Rossum can limit its learning capabilities. This is a priced feature and has no effect unless enabled. | 
delete_after | datetime | null | For internal use only (When a queue is marked for its deletion it will be done after this date) | true
status | string | active | Current status of the queue, seeQueue status | true
modified_by | URL | null | Last modifier. | true
modified_at | datetime | null | Time of last modification. | true
workflows | list[object] | [] | [BETA]Workflows set for the queue. Read more about the objectshere | 

More specific AI Core Engine parameters influencing the extraction may be set usingrir_paramsfield.
So far, these parameters are publicly available:
- effective_page_count(int): Limits the extraction to the firsteffective_page_countpages of the document.Useful to prevent data extraction from additional pages of unrelated, but included documents.Default: 32 (pages to be extracted from a document).
- tables(boolean): Allows disabling line item data extraction.Useful to speed up data extraction when line item details are not required, especially on long documents with large tables.Default: true (line items are being extracted).
effective_page_count(int): Limits the extraction to the firsteffective_page_countpages of the document.
- Useful to prevent data extraction from additional pages of unrelated, but included documents.
- Default: 32 (pages to be extracted from a document).
tables(boolean): Allows disabling line item data extraction.
- Useful to speed up data extraction when line item details are not required, especially on long documents with large tables.
- Default: true (line items are being extracted).
Thelocalefield is a hint for theAI Engineon how to resolve some ambiguous cases during data extraction, concerning e.g. date formats or decimal separators that may depend on the locale.  For example, in US the typical date format is mm/dd/yyyy whilst in Europe it is dd.mm.yyyy. A date such as "12. 6. 2018" will be extracted as Jun 12 when locale isen_GB, while the same date will be extracted as Dec 6 when locale isen_US.
For backward compatibility,webhooksattribute is an alias ofhooks. If both attributes are specified,webhooksoverrideshooks. For new integrations, do not specifywebhooksattribute.

#### Automation level

With queue attributeautomation_levelyou can set at which circumstances
should be annotation auto-exported after the AI-based data extraction, without
validation in the UI (skipping theto_reviewandreviewingstate).
Attribute can have following options:

Automation level | Description
--- | ---
always | Auto-export all documents with no validation errors. When there is an error triggered for a non-required field, such values are deleted and export is re-tried.
confident | Auto-export documents with at least onevalidation sourceand no validation errors.
never | Annotation is not automatically exported and must be validated in UI manually.


#### Queue status


Queue status | Description
--- | ---
active | This is the default status. Queue is usable.
deletion_requested | Queue is marked for deletion (by callingDELETE /v1/queues/<id>). Will be asynchronously deleted afterdelete_after.
deletion_in_progress | Queue is currently being deleted. When a queue has this status some raise conditions may occur as the related objects are being gradually deleted.
deletion_failed | Something wrong happened in the process of queue deletion. The queue may be in an inconsistent state.

Please note, that document import (via upload as well as email) is disabled while the queue status is one ofdeletion_requested,deletion_in_progress,deletion_failed.

#### Settings attribute


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
columns | list[object] | [] | (Deprecated, useannotation_list_tableinstead) List that contains schema ids to be shown on a dashboard. | 
hide_export_button | bool | true | Toggle to uncover "Export" button on dashboard (useful whenqueue.use_confirmed_state = true), which allows manual export of annotations inconfirmedstatus. | 
autopilot | object | null | Autopilot configuration describing which fields can be confirmed automatically. | 
accepted_mime_types | list[str] | [] | List ofMIME typeswhich can be uploaded to the queue. This can contain wildcards such asimage/*or exact type likeapplication/pdf. | 
asynchronous_export | bool | true | (Deprecated) Always set totrue. Theconfirmendpoint returns immediately and hooks' and connector'ssaveendpoint is called asynchronously later on. This value is used only when queue does not have a connector. | 
automation | object | {} | Queue automation settings, seeautomation settings | 
rejection_config | object | {default} | Queue rejection settings, seerejection settings | 
suggested_recipients_sources | list[object] | [{default}] | Queue suggested email recipients settings, seesuggested recipients settings | 
suggested_edit | str | disable | Allow to split document (semi-)automatically. Allowed values are:suggestanddisable. | 
dashboard_customization | object | {default} | Dashboard customization settings, seedashboard customization settings | 
email_notifications | object | {default} | Queue email notifications settings, seeemail notifications settings | 
workflows | object | {default} | [BETA]Please note that this can be modified only when the workflows addon is enabled (read more detailshere). | 
annotation_list_table | object | {} | Configuration of annotation dashboard columns | 
upload_values | list[object] | [] | Configuration of values to be specified duringupload(seedefinition of the object) | 
ui_upload_enabled | bool | true | Flag for enabling upload for particular queue in Rossum UI. | false
ui_on_edit_confirm | str | validate_first | Changes edit screen confirm button behavior. Allowed values are:annotation_list,edit_next,validate_first. | 
ui_validation_screen_enabled | bool | true | Flag for enabling validation screen for a particular queue in Rossum UI. If disabled, opening of a document will trigger a redirect to an edit screen. | false
ui_edit_values | list[object] | [] | Configuration of values to be specified duringedit_pages(seedefinition of the object) | 


#### Automation settings


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
automate_duplicates | bool | true | When set totrue, automation will be enabled for documents that have a duplicates. Disabled if parameter isfalse. | false
automate_suggested_edit | bool | false | When set totrue, automation will be enabled for annotations containingsuggested edits. Disabled if parameter isfalse. | false


#### Rejection settings


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
enabled | bool | true | DashboardRejectedis visible in application when enabled is set totrue. | false


#### Suggested recipients sources settings


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
source | string | email_header | Indicates source of the suggested recipients email address, seepossible sources. | false
schema_id | string |  | Used for finding appropriate datapoint value in annotation data (necessary only for vendor_database and extracted_value sources). | false


#### Suggested recipients possible sources


Source | Description
--- | ---
email_header | Email is taken from the sender in header of the email. See email onannotation.
extracted_value | Email is extracted from annotation data - schema_id is used to find requested value.
vendor_database | Email is extracted from annotation data - schema_id is used to find requested value. Value is filled by vendor matching connector.
queue_mailing_history | [BETA]Emails are taken from all the recipient inside all the emails send inside the email's queue. See email onannotation.
organization_users* | [BETA]Emails are taken from the users of related organization

- List of the organization users is filtered based on the role of an user that is requesting the data

#### Dashboard customization settings


Attribute | Type | Default | Description
--- | --- | --- | ---
all_documents | string | false | When set totrue, all UI tabs are merged into one, so the documents with different statuses are mixes in one tab instead of having its own one.
confirmed | bool | true | When set totrue, UI tab forconfirmeddocuments will be shown. Relates to the queue settings attributeuse_confirmed_stateis set to true.
deleted | bool | true | When set totrue, UI tab for documents indeletedstate will be shown.
exported | bool | true | When set totrue, UI tab for documents inexportedstate will be shown.
postponed | bool | true | When set totrue, UI tab for documents inpostponedstate will be shown.
rejected | bool | true | When set totrue, UI tab for documents inrejectedstate will be shown.
to_review | bool | true | When set totrue, UI tab for documents into_reviewstate will be shown.


#### Email notifications settings


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
recipient | object | None | Information about email address to send notifications to (e.g. about failed import). It contains keysemailandname. | false
unprocessable_attachments | bool | false | Whether return back unprocessable attachments (e.g. MS Word docx) or just silently ignore them. When true,minimum image sizerequirement does not apply. | false
postponed_annotations | bool | false | Whether to send notification when annotation is postponed. | false
deleted_annotations | bool | false | Whether to send notification when annotation is deleted. | false
email_with_no_attachments | bool | true | Whether to send notification when no processable documents were found. | false


Attribute | Type | Default | Read-only
--- | --- | --- | ---
recipient | object | None | false
unprocessable_attachments | bool | False | false
postponed_annotations | bool | False | false
deleted_annotations | bool | False | false
email_with_no_attachments | bool | True | false


#### Workflows settings


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
enabled | bool | false | DashboardWorkflowsis visible in application when enabled is set totrue. Also enables the workflow automation. | false
bypass_workflows_allowed | bool | false | Whether to allow toconfirmannotation with optionskip_workflows=true | 


#### Annotation list table configuration


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
columns | list[object] | [] | Configuration of columns on annotation dashboard (seedefinition of the object) | false


#### Annotation list table column configuration


Attribute | Type | Description
--- | --- | ---
visible | bool | Column is visible on the dashboard
width | float | Width of the column
column_type | enum | Type of the field (meta- annotation meta field,schema- annotation content field)
schema_id | string | schema_idof the extracted field (only forcolumn_type=schema)
data_type | enum | Data type of the extracted field (only forcolumn_type=schema). Allowed values aredate,number,string,boolean
meta_type | enum | Meta column type (only forcolumn_type=meta). Allowed values can be found inmeta_fieldtable(+ additionallydetails)


#### Upload values configuration

Value obtained from the user in the upload dialog may be passed as an upload value or in an annotationmetadatafield. SeeUploadfor details.

Attribute | Type | Description | Required | Default
--- | --- | --- | --- | ---
id | string | ID of the value | yes | 
type | string | Type of the value:valuesormetadata— specify how to pass the value | no | values
data_type | string | Data type of the value:enumorstring | no | string
label | string | Label to be used in UI | yes | 
enum_options | list[object] | List of objects withvalueandlabelfields. Only allowed forenumtype. | no | null
required | bool | Whether the value is required to be set during upload | no | false


#### UI Edit values configuration

Value obtained from the user in the edit screen may be passed as an edit value. SeeEdit pagesandSuggested Editfor details.

Attribute | Type | Description | Required | Default
--- | --- | --- | --- | ---
id | string | ID of the value | yes | 
label | string | Label to be used in UI | yes | 
data_type | string | Type of the value:enumorstring | yes | 
enum_options | list[object] | List of objects withvalueandlabelfields. Only allowed forenumdata_type. | no | null
required | bool | Whether the value is required to be set during edit | no | false

Schema Datapoint descriptiondescribes how edit values are used to initialize datapoint values.

#### Queue workflows


Attribute | Type | Description | Read-only
--- | --- | --- | ---
url | url | Url of the workflow object | false
priority | integer | Priority of the linked workflow. Designate the order of their evaluation (lower number means it's evaluated sooner) | false


### Import a document

> Upload file using a form (multipart/form-data)
Upload file using a form (multipart/form-data)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

> Upload file in a request body
Upload file in a request body

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

> Upload file in a request body (UTF-8 filename must be URL encoded)
Upload file in a request body (UTF-8 filename must be URL encoded)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H"Content-Disposition: attachment; filename*=utf-8''document%20%F0%9F%8E%81.pdf"--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

> Upload file in a request body with a filename in URL (UTF-8 filename must be URL encoded)
Upload file in a request body with a filename in URL (UTF-8 filename must be URL encoded)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload/document%20%F0%9F%8E%81.pdf'
```

> Upload multiple files using multipart/form-data
Upload multiple files using multipart/form-data

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document1.pdf-Fcontent=@document2.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

> Upload file using basic authentication
Upload file using basic authentication

```
curl-u'east-west-trading-co@<example>.rossum.app:secret'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

> Upload file with additional field values and metadata
Upload file with additional field values and metadata

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\-Fvalues='{"upload:organization_unit":"Sales"}'\-Fmetadata='{"project":"Market ABC"}'\'https://<example>.rossum.app/api/v1/queues/8236/upload'
```

POST /v1/queues/{id}/upload
POST /v1/queues/{id}/upload/{filename}
Uploads a document to the queue (starting in theimporting state). This
creates adocumentobject and an emptyannotationobject.
The file can be sent as a part of multipart/form-data or, alternatively, in the
request body. Multiple files upload is supported, the total size of the data uploaded may not exceed 40 MB.
UTF-8 filenames are supported, see examples.
You can also specify additional properties using form field:
- metadata could be passed usingmetadataform field. Metadata will
be set to newly created annotation object.
- values could be passed usingvaluesform field. It may
be used to initialize datapoint values by setting the value ofrir_field_namesin the schema.
For exampleupload:organization_unitfield may be referenced in a schema like this:{
     "category": "datapoint",
     "id": "organization_unit",
     "label": "Org unit",
     "type": "string",
     "rir_field_names": ["upload:organization_unit"]
     ...
   }

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

Response contains a list of annotations and documents created. Top-level keysannotationanddocumentare obsolete and should be ignored.
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

> Download CSV file with selected columns from annotations315777and315778.
Download CSV file with selected columns from annotations315777and315778.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=csv&columns=meta_file_name,document_id,date_issue,sender_name,amount_total&id=315777,315778'
```


```
meta_file_name,Invoice number,Invoice Date,Sender Name,Total amount
template_invoice.pdf,12345,2017-06-01,"Peter, Paul and Merry",900.00
quora.pdf,2183760194,2018-08-06,"Quora, Inc",500.00
```

> Download CSV file with prepend_columns and append_columns from annotations315777and315778.
Download CSV file with prepend_columns and append_columns from annotations315777and315778.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=csv&prepend_columns=meta_file_name&append_columns=meta_url&id=315777,315778'
```


```
meta_file_name,Invoice number,Invoice Date,Sender Name,Total amount,meta_url
template_invoice.pdf,12345,2017-06-01,"Peter, Paul and Merry",900.00,https://<example>.rossum.app/api/v1/annotations/315777
quora.pdf,2183760194,2018-08-06,"Quora, Inc",500.00,https://<example>.rossum.app/api/v1/annotations/315778
```

> Download CSV file for a specific page when downloading large amounts of data.
Download CSV file for a specific page when downloading large amounts of data.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=csv&status=exported&page=1&page_size=1000'
```

> Download XML file with all exported annotations
Download XML file with all exported annotations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=xml&status=exported'
```


```
<?xml version="1.0" encoding="utf-8"?><export><results><annotationurl="https://<example>.rossum.app/api/v1/annotations/315777"><status>exported</status><arrived_at>2019-10-13T21:33:01.509886Z</arrived_at><exported_at>2019-10-13T12:00:01.000133Z</exported_at><documenturl="https://<example>.rossum.app/api/v1/documents/315877"><file_name>template_invoice.pdf</file_name><file>https://<example>.rossum.app/api/v1/documents/315877/content</file></document><modifier/><schemaurl="https://<example>.rossum.app/api/v1/schemas/31336"/><metadata/><content><sectionschema_id="invoice_details_section"><datapointschema_id="document_id"type="string"rir_confidence="0.99">12345</datapoint>...</section></content></annotation></results><pagination><next/><previous/><total>1</total><total_pages>1</total_pages></pagination></export>
```

> Download JSON file with all exported annotations that were imported on October 13th 2019.
Download JSON file with all exported annotations that were imported on October 13th 2019.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?format=json&status=exported&arrived_at_after=2019-10-13&arrived_at_before=2019-10-14'
```


```
{"pagination":{"total":5,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/annotations/315777","status":"exported","arrived_at":"2019-10-13T21:33:01.509886Z","exported_at":"2019-10-14T12:00:01.000133Z","document":{"url":"https://<example>.rossum.app/api/v1/documents/315877","file_name":"template_invoice.pdf","file":"https://<example>.rossum.app/api/v1/documents/315877/content"},"modifier":null,"schema":{"url":"https://<example>.rossum.app/api/v1/schemas/31336"},"metadata":{},"content":[{"category":"section","schema_id":"invoice_details_section","children":[{"category":"datapoint","schema_id":"document_id","value":"12345","type":"string","rir_confidence":0.99},...]}]}]}
```

> Download and set the status of annotations toexporting.
Download and set the status of annotations toexporting.

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/export?to_status=exporting&status=confirmed'
```


```
{"pagination":{"total":5,"total_pages":1,"next":null,"previous":null},"results":[{"status":"exporting",...}]}
```

GET /v1/queues/{id}/exportorPOST /v1/queues/{id}/export
Export annotations from the queue in XML, CSV or JSON format.
Output format is negotiated by Accept header orformatparameter. Supported formats are:csv,xml,xlsxandjson.

#### Filters

Filters may be specified to limit annotations to be exported, all filters applicable to theannotation listare supported.
Multiple filter attributes are combined with AND, which results in more specific response.
The most common filters are eitherlist of idsor specifying atime period:

Attribute | Description
--- | ---
id | Id of annotation to be exported, multiple ids may be separated by a comma.
status | Annotationstatus
modifier | User id
arrived_at_before | ISO 8601 timestamp (e.g.arrived_at_before=2019-11-15)
arrived_at_after | ISO 8601 timestamp (e.g.arrived_at_after=2019-11-14)
exported_at_before | ISO 8601 timestamp (e.g.exported_at_before=2019-11-14 22:00:00)
exported_at_after | ISO 8601 timestamp (e.g.exported_at_after=2019-11-14 12:00:00)
export_failed_at_before | ISO 8601 timestamp (e.g.export_failed_at_before=2019-11-14 22:00:00)
export_failed_at_after | ISO 8601 timestamp (e.g.export_failed_at_after=2019-11-14 12:00:00)
page_size | Number of the documents to be exported. To be used together withpageattribute. Seepagination.
page | Number of a page to be exported when using pagination. Useful for exports of large amounts of data. To be used together with thepage_sizeattribute.
to_status | statusof annotations under export is switched to definedto_statusstate (useful whenqueue.use_confirmed_state = true). This parameter is only valid with POST method,statuscan be changed only toexporting(export will be initiated asynchronously and status will be moved toexportedautomatically after successful export) orexported(export will be initiated sychronously). Annotations with current statusexportedorexportingare left untouched.


#### Response

Returnspaginatedresponse that contains annotation data in one of the following format.
Columns included in CSV output are defined bycolumns,prepend_columnsandappend_columnsURL parameters.prepend_columnsparameter defines columns at the beginning of the row whileappend_columnsat the end. All stated parameters
are specified by datapoint schema ids and meta-columns. Default is to export
all fields defined in a schema.
Supported meta-columns are:meta_arrived_at,meta_file,meta_file_name,meta_status,meta_url,meta_automated,meta_modified_at,meta_assigned_at.
CSV format can be fine-tuned by following query parameters:
- delimiter- one-character string used to separate fields. It defaults to ','.
- quote_char- one-character string used to quote fields containing special characters, such as the delimiter or quotechar, or which contain new-line characters. It defaults to '"'.
- quoting- controls when quotes should be generated by the writer and recognised by the reader. It can take on any of thequote_minimal,quote_none,quote_all,quote_non_numeric. Ifquote_noneis specified,escape_charis mandatory.
- escape_char- one-character string used by the writer to escape the delimiter.
XLSX export behaves exactly same as CSV export, including URL parameters.
The only difference is output format.
XML format is described by XML Schema Definitionqueues_export.xsd.
JSON format uses format similar to the XML format above.

### Get suggested email recipients

> Get315777,78590annotations and7524email_hooks suggested email recipients
Get315777,78590annotations and7524email_hooks suggested email recipients

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/315777", https://<example>.rossum.app/api/v1/annotations/78590], "email_threads": ["https://<example>.rossum.app/api/v1/email_threads/7524"]}'\'https://<example>.rossum.app/api/v1/queues/246/suggested_recipients'
```


```
{"results":[{"source":"email_header","email":"don.joe@corp.us","name":"Don Joe"},...]}
```

POST /v1/queues/{id}/suggested_recipients
Retrieves suggested email recipients depending on Queuessuggested recipients settings.

Attribute | Type | Description
--- | --- | ---
annotations | list | List ofannotationurls
email_threads | list | List ofemail threadurls


#### Response

Returns a list ofsource objects.

#### Suggested recipients source object


Parameter | Description
--- | ---
source | Specifies where the email is found, seepossible sources
email | Email address of the suggested recipient
name | Name of the suggested recipient. Either a value from an email header or a value from parsing the email address


### List all queues

> List all queues in workspace7540ordered byname
List all queues in workspace7540ordered byname

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues?workspace=7540&ordering=name'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":8199,"name":"Receipts","url":"https://<example>.rossum.app/api/v1/queues/8199","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540",...},{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540",...}]}
```

Retrieve all queue objects.
Supported ordering:id,name,workspace,connector,webhooks,schema,inbox,locale

#### Filters


Attribute | Description
--- | ---
id | Id of a queue
name | Name of a queue
workspace | Id of a workspace
inbox | Id of an inbox
connector | Id of a connector
webhooks | Ids of hooks
hooks | Ids of hooks
locale | Queue object locale
dedicated_engine | Id of a dedicated engine
generic_engine | Id of a generic engine
deleting | Bool filter - queue is being deleted (delete_afteris set)


#### Response

Returnspaginatedresponse with a list ofqueueobjects.

### Create new queue

> Create new queue in workspace7540namedTest Queue
Create new queue in workspace7540namedTest Queue

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Queue", "workspace": "https://<example>.rossum.app/api/v1/workspaces/7540", "schema": "https://<example>.rossum.app/api/v1/schemas/31336", "generic_engine": "https://<example>.rossum.app/api/v1/generic_engines/9876"}'\'https://<example>.rossum.app/api/v1/queues'
```


```
{"id":8236,"name":"Test Queue","url":"https://<example>.rossum.app/api/v1/queues/8236","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876",...}
```

Create a newqueueobject.

#### Response

Returns createdqueueobject.

#### Create queue from template organization

Create new queue object from template organization, see available templates inorganization.
> Create new queue object from template organization
Create new queue object from template organization

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test queue", "template_name": "EU Demo Template", "workspace": "https://<example>.rossum.app/api/v1/workspaces/489", "include_documents": false}'\'https://<example>.rossum.app/api/v1/queues/from_template'
```


```
{"id":8236,"name":"Test Queue","url":"https://<example>.rossum.app/api/v1/queues/8236",...}
```

POST /v1/queues/from_template
Create a new queue object.

Attribute | Description
--- | ---
name | Name of a queue
template_name | Template to use for new queue
workspace | Id of a workspace
include_documents | Whether to copy documents from the template queue


#### Response

Returns createdqueueobject.

### Retrieve a queue

> Get queue object8198

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8198'
```


```
{"id":8198,"name":"Received invoices","url":"https://<example>.rossum.app/api/v1/queues/8198","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876",...}
```


#### Response


### Update a queue

> Update queue object8236
Update queue object8236

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "My Queue", "workspace": "https://<example>.rossum.app/api/v1/workspaces/7540", "schema": "https://<example>.rossum.app/api/v1/schemas/31336", "generic_engine": "https://<example>.rossum.app/api/v1/generic_engines/9876"}'\'https://<example>.rossum.app/api/v1/queues/8236'
```


```
{"id":8236,"name":"My Queue","url":"https://<example>.rossum.app/api/v1/queues/8236","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540","generic_engine":"https://<example>.rossum.app/api/v1/generic_engines/9876",...}
```


#### Response

Returns updatedqueueobject.

### Update part of a queue

> Update name of queue object8236
Update name of queue object8236

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "New Queue"}'\'https://<example>.rossum.app/api/v1/queues/8236'
```


```
{"id":8236,"name":"New Queue","url":"https://<example>.rossum.app/api/v1/queues/8236","workspace":"https://<example>.rossum.app/api/v1/workspaces/7540",...}
```

PATCH /v1/queues/{id}
Update part of queue object.

#### Response

Returns updatedqueueobject.

### Duplicate a queue

> Duplicate existing queue object8236
Duplicate existing queue object8236

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Duplicate Queue", "copy_extensions_settings": true, "copy_email_settings": true, "copy_automation_setting": true, "copy_permissions": true, "copy_rules_and_actions": true}'\'https://<example>.rossum.app/api/v1/queues/8236/duplicate'
```


```
{"id":8237,"name":"Duplicate Queue","url":"https://<example>.rossum.app/api/v1/queues/8237",...}
```

POST /v1/queues/{id}/duplicate
Duplicate a queue object.

Attribute | Type | Default | Description
--- | --- | --- | ---
name | string |  | Name of the duplicated queue.
copy_extensions_settings | bool | true | Whether to copyhooks.
copy_email_settings | bool | true | Whether to copyemail notifications settings.
copy_delete_recommendations | bool | true | Whether to copydelete recommendations.
copy_automation_settings | bool | true | Whether to copyautomation level,automation settingsandautomation_enabledqueue settingssettings.
copy_permissions | bool | true | Whether to copyusersandmemberships.
copy_rules_and_actions | bool | true | Whether to copyrules.


#### Response

Returns duplicate ofqueueobject.

### Delete a queue

> Delete queue8236

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236'
```

DELETE /v1/queues/{id}
Calling this endpoint will schedule the queue to be asynchronously deleted. The only synchronous operations are
- setdelete_after
- changestatustodeletion_requested(seequeue status)
- unlink workspace
- the above will result in queue not being visible in the Rossum UI
- importing docs to the queue is disabled (viauploadas well asemail import)
By default, the deletion will start after 24 hours. You can change this behaviour by specifyingdelete_afterquery parameter.

#### Query parameters


Key | Type | Default value | Description
--- | --- | --- | ---
delete_after | timedelta | 24:00:00 | The queue deletion will be postponed by the given time delta.


#### Response


### Start annotation

POST /v1/queues/{id}/next
Start reviewing the next available annotation from the queue by the calling user.
This endpoint isINTERNALand may change in the future.

Attribute | Type | Description
--- | --- | ---
annotation_ids | list[integer] | List of annotation ids to select from (optional).
statuses | list[string] | List of allowed statuses (optional).


#### Response


Attribute | Type | Description
--- | --- | ---
annotation | URL | URL of started annotation.
session_timeout | string | Session timeout in format HH:MM:SS.

If there is no annotation to start status200is returned with body:{"annotation": null}

### Get counts of related objects

> Get counts of related objects for queue8236
Get counts of related objects for queue8236

```
curl-XGET-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/queues/8236/related_objects_counts'
```


```
{"annotations":123,"emails":456,"trained_dedicated_engines":2}
```

GET /v1/queues/{id}/related_objects_counts
Get counts of selected related objects for a queue.

Attribute | Type | Description
--- | --- | ---
emails | integer | Number of email objects related to the queue
annotations | integer | Number of annotation objects related to the queue (purged annotations are excluded from this count)
trained_dedicated_engines | integer | Number of dedicated engines using the queue for training


#### Response


## Relation

> Example relation object
Example relation object

```
{"id":1,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/1"}
```

A relation object introduce common relations between annotations. An annotation could be related to one or more other annotations and
it may belong to several relations at the same time.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the relation | true
type | string | edit | Type of relationship. Possible values areedit,attachmentorduplicate. Seebelow | 
key | string |  | Key used to distinguish several instances of the same type | 
parent | URL |  | URL of the parent annotation in case of 1-M relationship | 
annotations | list[URL] |  | List of related annotations | 
url | URL |  | URL of the relation | true


#### Relation types:

- editrelation is created after editing annotation in user interface (rotation or split of the document). The original annotation is set toparentattribute and newly created
annotations are set toannotationsattribute. To find all siblings of edited annotation seefilters on annotation
- attachmentis a relationship representing the state that one or more documents are attachments to another document.keyis null in this case. Feature must be enabled.
- duplicaterelation is created after importing the same document that already exists in Rossum for current organization.
Ifduplicaterelation already exists then corresponding annotation is added to existing relation.keyofduplicaterelation is set to MD5 hash of document content.
To find all duplicates of the annotation filter annotations with appropriate MD5 hash in relationkey. Seefilters on annotation

### List all relations

> List all relations

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/relations'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/456","https://<example>.rossum.app/api/v1/annotations/457"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}]}
```

Retrieve all relation objects (annotations from queues not withactivestatusare excluded).

Attribute | Description
--- | ---
id | Id of the relation. Multiple values may be separated using a comma.
type | Relationtype. Multiple values may be separated using a comma.
parent | Id of parent annotation. Multiple values may be separated using a comma.
key | Relation key
annotation | Id of related annotation. Multiple values may be separated using a comma.

Supported ordering:type,parent,key
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofrelationobjects.

### Create a new relation

> Create a new relation of type edit
Create a new relation of type edit

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "edit", "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124"]}'\'https://<example>.rossum.app/api/v1/relations'
```


```
{"id":789,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124"],"url":"https://<example>.rossum.app/api/v1/relations/789"}
```

> Create a new attachment. Annotation 123 will have an attachment 124.
Create a new attachment. Annotation 123 will have an attachment 124.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "attachment", "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124"]}'\'https://<example>.rossum.app/api/v1/relations'
```


```
{"id":787,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124"],"url":"https://<example>.rossum.app/api/v1/relations/787"}
```

Create a new relation object.

#### Response

Returns createdrelationobject.

### Retrieve a relation

> Get relation object1500
Get relation object1500

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/relations/1500'
```


```
{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}
```

GET /v1/relations/{id}
Get an relation object.

#### Response

Returnsrelationobject.

### Update a relation

> Update the relation object1500
Update the relation object1500

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "edit", "key": None, "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124"} \
  'https://<example>.rossum.app/api/v1/relations/1500'
```


```
{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}
```

> Attachment update. Annotation 123 will have two attachments: 124 and 125.
Attachment update. Annotation 123 will have two attachments: 124 and 125.

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"type": "attachment", "parent": "https://<example>.rossum.app/api/v1/annotations/123", "annotations": ["https://<example>.rossum.app/api/v1/annotations/124", "https://<example>.rossum.app/api/v1/annotations/125"]}'\'https://<example>.rossum.app/api/v1/relations/787'
```


```
{"id":787,"type":"attachment","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/787"}
```

PUT /v1/relations/{id}
Update relation object.

#### Response

Returns updatedrelationobject.

### Update part of a relation

> Update relation annotations on relation object1500
Update relation annotations on relation object1500

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/124", "https://<example>.rossum.app/api/v1/annotations/125"]}'\'https://<example>.rossum.app/api/v1/relations/1500'
```


```
{"id":1500,"type":"edit","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/124","https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/1500"}
```

> Attachment partial update. Annotation 123 will have just one attachment 125.
Attachment partial update. Annotation 123 will have just one attachment 125.

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotations": ["https://<example>.rossum.app/api/v1/annotations/125"]}'\'https://<example>.rossum.app/api/v1/relations/787'
```


```
{"id":787,"type":"attachment","key":null,"parent":"https://<example>.rossum.app/api/v1/annotations/123","annotations":["https://<example>.rossum.app/api/v1/annotations/125"],"url":"https://<example>.rossum.app/api/v1/relations/787"}
```

PATCH /v1/relations/{id}
Update part of relation object.

#### Response

Returns updatedrelationobject.

### Delete a relation

> Delete relation1500

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/relations/1500'
```

DELETE /v1/relations/{id}
Delete relation object.

#### Response


## Rule

> Example rule object

```
{"id":123,"url":"https://<example>.rossum.app/api/v1/rules/123","name":"rule","enabled":true,"organization":"https://<example>.rossum.app/api/v1/organizationss/1001","schema":"https://<example>.rossum.app/api/v1/schemas/1001","trigger_condition":"True","created_by":"https://<example>.rossum.app/api/v1/users/9524","created_at":"2022-01-01T15:02:25.653324Z","modified_by":"https://<example>.rossum.app/api/v1/users/2345","modified_at":"2020-01-01T10:08:03.856648Z","rule_template":null,"synchronized_from_template":false,"actions":[{"id":"f3c43f16-b5f1-4ac8-b789-17d4c26463d7","enabled":true,"type":"show_message","payload":{"type":"error","content":"Error message!","schema_id":"invoice_id"},"event":"validation"}]}
```

Rule object represents arbitrary business rules added toschemaobjects.

Attribute | Type | Read-only | Description
--- | --- | --- | ---
id | integer | yes | Rule object ID.
url | URL | yes | Rule object URL.
name | string | no | Name of the rule.
trigger_condition | string | no | A condition for triggering the rule's actions. (default:"True"). This is a formula evaluated byRossum TxScript.
organization | URL | yes | Organization the rule belongs to.
schema | URL | no | Schema the rule belongs to.
rule_template | URL | no | (optional) Rule template the rule was created from.
synchronized_from_template | bool | no | Signals whether the rule is automatically updated from the linked template. (default:false)
created_by | URL | no | User who created the rule.
created_at | datetime | no | Timestamp of the rule creation.
modified_by | URL | no | User who was the last to modify the rule.
modified_at | datetime | no | Timestamp of the latest modification.
actions | list[object] | no | List of the rule action objects (Seerule actions.
enabled | bool | no | If false the rule is disabled (default:true)


### Trigger condition

Thetrigger_conditionis aTxScriptformula which controls the execution of the list of actions in a rule object.
There are two possible evaluation modes for this condition:
- simple mode: when the condition does not reference any datapoint, or only reference header fields. Example:len(field.document_id) < 10.
- line-item mode: when the condition references a line item datapoint (a column of a multivalue table). Examplefield.item_amount > 100.0.
In line item mode, the condition is evaluatedonce for each row of the table, which means multiple actions can potentially be executed. In this case, a deduplication mechanism prevents the creation of duplicate messages (show_messageaction), duplicate blockers (add_automation_blockeraction), and identical emails from being sent (send_emailaction).

### Rule actions

Object defines rule actions to be executed when trigger condition is met.

Attribute | Type | Read-only | Description
--- | --- | --- | ---
id | string | no | Rule action ID. Needs to be unique within the Rule'sactions.
enabled | bool | no | If false the action is disabled (default:true).
type | string | no | See the following for the list of possible actions.
payload | object | no | See the following for the payload structure for each action.
event | object | no | Actions are configured to be executed on a specific event, seetrigger events.

Note that just after document import, the initial validation is performed and rules are then executed: 
the trigger conditions are first evaluated on the latest anntoation content, and then actions registered onvalidationandannotation_importedevents are both executed.

#### Action Show message

Event: can be triggered onvalidationevent only.

Attribute | Type | Description
--- | --- | ---
type | string | One of:error,warning,info.
content | string | Message content to be displayed.
schema_id | Optional[string] | Optional message target field (omit for document scope message).


#### Action Add automation blocker

Action:add_automation_blocker
Event: can be triggered onvalidationevent only.

Attribute | Type | Description
--- | --- | ---
content | string | Automation blocker content to be displayed.
schema_id | Optional[string] | Optional automation blocker target field id (omit for document scope automation blocker).

Note: at most one action of typeadd_automation_blockercan be set up for oneruleobject.

#### Action change status

Event: can be triggered onannotation_importedevent only.

Attribute | Type | Description
--- | --- | ---
method | string | Possible options:postpone,export,delete,confirm,reject.

Note: at most one action of typechange_statuscan be set up for oneruleobject.

#### Action Change queue

This action moves the annotation to another queue with or without re-extraction of the data (see thereimportflag).
Event: Can be configured to trigger onannotation_imported,annotation_confirmedorannotation_exported.

Attribute | Type | Description
--- | --- | ---
reimport | Optional[bool] | Flag that controls whether the annotation will be reimported during the action execution.
queue_id | integer | ID of the target queue.

Note: at most one action of typechange_queuecan be set up for oneruleobject.

#### Action Add label

Event: can be triggered onvalidationevent only.

Attribute | Type | Description
--- | --- | ---
labels | list[url] | URLs oflabelobject to be linked to the processedannotation.

Note: at most one action of typeadd_labelcan be set up for oneruleobject.

#### Action Remove label

Event: can be triggered onvalidationevent only.

Attribute | Type | Description
--- | --- | ---
labels | list[url] | URLs oflabelobject to be unlinked from the processedannotation.

Note: at most one action of typeremove_labelcan be set up for oneruleobject.

#### Action Add / Remove label

Action:add_remove_label
Event: can be triggered onvalidationevent only.

Attribute | Type | Description
--- | --- | ---
labels | list[url] | URLs oflabelobject to be linked to the processedannotation.

The affected labels are added to the annotation when the condition is satisfied, and removed otherwise.
Note: at most one action of typeadd_remove_labelcan be set up for oneruleobject.

#### Action Show / hide field

Action:show_hide_field
Event: can be triggered onvalidationevent only.

Attribute | Type | Description
--- | --- | ---
schema_ids | List[string] | Sethiddenattribute of schema fields according to condition. (Please seeschema content).

The affected schema field is visible when the condition is satisfied, and is hidden otherwise.

#### Action Show field

Event: can be triggered onvalidationevent only.

Attribute | Type | Description
--- | --- | ---
schema_ids | List[string] | Sethiddenattribute of schema fields toFalse. (Please seeschema content).

Note: at most one action of typeshow_fieldcan be set up for oneruleobject.

#### Action Hide field

Event: can be triggered onvalidationevent only.

Attribute | Type | Description
--- | --- | ---
schema_ids | List[string] | Sethiddenattribute of schema fields toTrue. (Please seeschema content).

Note: at most one action of typehide_fieldcan be set up for oneruleobject.

#### Action Add validation source

Addsrulesvalidation source to a datapoint.
Action:add_validation_source
Event: can be triggered onvalidationevent only.

Attribute | Type | Description
--- | --- | ---
schema_id | string | Schema ID of the datapoint to add the validation source to (Please seeschema content).

Note: at most one action of typeadd_validation_sourcecan be set up for oneruleobject.

#### Action send email

In line item mode of execution, deduplication mechanism will prevent multiple identical emails from being sent, and at mostfiveemails can be sent by a single action.
Event: Can be configured to trigger onannotation_imported,annotation_confirmedorannotation_exported.
Ifemail_templateis defined, the rest of the attributes are ignored.

Attribute | Type | Description | Required
--- | --- | --- | ---
email_template | string | Email template URL. | Yes
attach_document | boolean | When true document linked to the annotation will be sent together with the email as an attachment (defaultFalse). | No

Ifemail_templateis not defined, then the payload can contain the following attributes:

Attribute | Type | Description | Required
--- | --- | --- | ---
to | List[string] | List of recipients. | Yes
subject | string | Subject of the email. | Yes
body | string | Body of the email. | Yes
cc | List[string] | List of cc. | No
bcc | List[string] | List of bcc. | No


### List all rules

> List all rules

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/rules'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/rules/1",...}]}
```

List all rules objects.
Supported filters:id,queue,enabled,linked,actions,schema,rule_template,name,organization
Supported ordering:id,name,organization

Filter | Type | Description
--- | --- | ---
actions | list[str] | Comma separated list of action types (e.g.show_message,change_queue)
linked | boolean | List onlylinked/unlinkedrules (linked rules have more than one queue connected)
enabled | boolean | List onlyenabled/disabledrules
queue | list[int] | List rules by queue ids
id | list[int] | List rules by rule ids

For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofruleobjects.

### Retrieve rule

> Get rule object123

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/rules/123'
```


```
{"id":123,"url":"https://<example>.rossum.app/api/v1/rules/123",...}
```

Retrieve a rule object.

#### Response


### Create a new rule

> Create new rule

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "rule", "organization": "https://<example>.rossum.app/api/v1/organization/1", "schema": "https://<example>.rossum.app/api/v1/schemas/442"}'\'https://<example>.rossum.app/api/v1/rules'
```


```
{"id":42,"url":"https://<example>.rossum.app/api/v1/rules/42",...}
```

Create a new rule object.

#### Response

Returns createdruleobject.

### Update part of a rule

> Update content of rule object42
Update content of rule object42

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Block automation when invoice is missing"}'\'https://<example>.rossum.app/api/v1/rules/42'
```


```
{"id":42,"url":"https://<example>.rossum.app/api/v1/rules/42",...}
```

Update part of rule object.

#### Response

Returns updatedruleobject.

### Update a rule

> Update rule object42

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "rule", "organization": "https://<example>.rossum.app/api/v1/organization/1", "schema": "https://<example>.rossum.app/api/v1/schemas/442"}'\'https://<example>.rossum.app/api/v1/rules/42'
```


```
{"id":42,"url":"https://<example>.rossum.app/api/v1/rules/42",...}
```


#### Response

Returns updatedruleobject.

### Delete a rule

> Delete rule42

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/rules/42'
```

DELETE /v1/rules/{id}

#### Response


## Schema

> Example schema object
Example schema object

```
{"id":31336,"name":"Basic Schema","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"url":"https://<example>.rossum.app/api/v1/schemas/31336","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","description":"section description","children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"],"constraints":{"required":false},"default_value":null},...]},...],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

A schema object specifies the set of datapoints that are extracted from the
document. For more information seeDocument Schema.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the schema | true
name | string |  | Name of the schema (not visible in UI) | 
url | URL |  | URL of the schema | true
queues | list[URL] |  | List of queues that use schema object. | true
content | list[object] |  | List of sections (top-level schema objects, seeDocument Schemafor description of schema) | 
metadata | object | {} | Client data. | 
modified_by | URL | null | Last modifier. | true
modified_at | datetime | null | Date of last modification. | true


### Validate a schema

> Validate content of schema object
Validate content of schema object

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","icon": null,"children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"]}]}]}'\'https://<example>.rossum.app/api/v1/schemas/validate'
```

POST /v1/schemas/validate
Validate schema object, check for errors.

#### Response

Returns 200 and error description in case of validation failure.

### List all schemas

> List all schemas

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/schemas'
```


```
{"pagination":{"total":2,"total_pages":1,"next":null,"previous":null},"results":[{"id":31336,"url":"https://<example>.rossum.app/api/v1/schemas/31336"},{"id":33725,"url":"https://<example>.rossum.app/api/v1/schemas/33725"}]}
```

Retrieve all schema objects.
Supported filters:id,name,queue
Supported ordering:id
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofschemaobjects.

### Create a new schema

> Create new empty schema
Create new empty schema

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Schema", "content": []}'\'https://<example>.rossum.app/api/v1/schemas'
```


```
{"id":33725,"name":"Test Schema","queues":[],"url":"https://<example>.rossum.app/api/v1/schemas/33725","content":[],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

Create a new schema object.

#### Response

Returns createdschemaobject.

#### Create schema from template organization

Create new schema object from template organization, see available templates inorganization.
> Create new schema object from template organization
Create new schema object from template organization

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Schema", "template_name": "EU Demo Template"}'\'https://<example>.rossum.app/api/v1/schemas/from_template'
```


```
{"name":"Test Schema","id":33726,"queues":[],"url":"https://<example>.rossum.app/api/v1/schemas/33726","content":[{"id":"invoice_info_section","icon":null,"label":"Basic information","category":"section","children":[...]}],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

POST /v1/schemas/from_template
Create a new schema object.

#### Response

Returns createdschemaobject.

### Retrieve a schema

> Get schema object31336
Get schema object31336

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/schemas/31336'
```


```
{"id":31336,"name":"Basic schema","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"url":"https://<example>.rossum.app/api/v1/schemas/31336","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","description":"section description","children":[{"category":"datapoint","id":"document_id","label":"Invoice number","description":"datapoint description","type":"string","rir_field_names":["document_id"],"constraints":{"required":false},"default_value":null},...]},...]}
```


#### Response


### Update a schema

> Update content of schema object33725
Update content of schema object33725

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name":"Test Schema","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","icon": null,"children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"]}]}]}'\'https://<example>.rossum.app/api/v1/schemas/33725'
```


```
{"id":33725,"name":"Test Schema","queues":[],"url":"https://<example>.rossum.app/api/v1/schemas/33725","content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"],"default_value":null}],"icon":null}],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

Update schema object. SeeUpdating schemafor more details about consequences of schema update.

#### Response

Returns updatedschemaobject.

### Update part of a schema

> Update  schema object31336
Update  schema object31336

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"content":[{"category":"section","id":"invoice_details_section","label":"Invoice details","icon": null,"children":[{"category":"datapoint","id":"document_id","label":"Invoice number","type":"string","rir_field_names":["document_id"]}]}]}'\'https://<example>.rossum.app/api/v1/schemas/31336'
```


```
{"id":31336,"name":"New Schema","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"url":"https://<example>.rossum.app/api/v1/schemas/31336","content":[],"metadata":{},"modified_by":"https://<example>.rossum.app/api/v1/users/1","modified_at":"2020-01-01T10:08:03.856648Z"}
```

PATCH /v1/schemas/{id}
Update part of schema object. SeeUpdating schemafor more details about consequences of schema update.

#### Response

Returns updatedschemaobject.

### Delete a schema

> Delete schema31336

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/schemas/31336'
```

DELETE /v1/schemas/{id}
Delete schema object.

#### Response


## Suggested edit

> Example suggested edit object
Example suggested edit object

```
{"id":314528,"url":"https://<example>.rossum.app/api/v1/suggested_edits/314528","annotation":"https://<example>.rossum.app/api/v1/annotations/314528","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314554","rotation":0},{"page":"https://<example>.rossum.app/api/v1/pages/314593","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}},{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314556","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}}]}
```

A suggested edit object contains splittings of incomming document suggested by the AI engine.
Suggested edit objects are created automatically during document import.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the suggested edit. | True
url | URL |  | URL of the suggested edit. | True
annotation | URL |  | Annotation that suggested edit is related to. | 
documents | list[Document split descriptor] |  | List of document split descriptors. | 


### Document split descriptor


Attribute | Type | Default | Description
--- | --- | --- | ---
pages | list[Page descriptor] |  | List of pages that should be split.
target_queue | URL |  | Target queue for the suggested split.
values | object | {} | Edit valuesto be propagated to newly created annotations. Keys must be prefixed with "edit:", e.g. "edit:document_type".Schema Datapoint descriptiondescribes how it is used to initialize datapoint value.


### Page descriptor


Attribute | Type | Default | Description
--- | --- | --- | ---
page | URL |  | Page to split.
rotation | integer | 0 | Rotation of the page.
deleted | boolean | false | Indicates whether the page is marked as deleted.


### List all suggested_edit objects

> List all suggested_edit objects
List all suggested_edit objects

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/suggested_edits'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":314528,"url":"https://<example>.rossum.app/api/v1/suggested_edits/314528","annotation":"https://<example>.rossum.app/api/v1/annotations/314528","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314554","rotation":0},{"page":"https://<example>.rossum.app/api/v1/pages/314593","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}},{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314556","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528""values":{"edit:document_type":"invoice"}}]}]}
```

GET /v1/suggested_edits
Retrieve all suggested edit objects.
Supported filters:annotation
Supported ordering:annotation
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofsuggested editobjects.

### Create a new suggested edit

> Create new suggested_edit
Create new suggested_edit

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotation": "https://<example>.rossum.app/api/v1/annotations/123", "documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/123"}]}]}'\'https://<example>.rossum.app/api/v1/suggested_edits'
```


```
{"id":123,"url":"https://<example>.rossum.app/api/v1/suggested_edits/123","annotation":"https://<example>.rossum.app/api/v1/annotations/123","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/123"}],"target_queue":"https://<example>.rossum.app/api/v1/queues/123","values":{}}]}
```

POST /v1/suggested_edits
Create a new suggested edit object.

#### Response

Returns createdsuggested editobject.

### Retrieve a suggested edit

> Get suggested edit object558598
Get suggested edit object558598

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/suggested_edits/558598'
```


```
{"id":314528,"url":"https://<example>.rossum.app/api/v1/suggested_edits/314528","annotation":"https://<example>.rossum.app/api/v1/annotations/314528","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314554","rotation":0},{"page":"https://<example>.rossum.app/api/v1/pages/314593","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}},{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/314556","rotation":0}],"target_queue":"https://<example>.rossum.app/api/v1/queues/314528","values":{}}]}
```

GET /v1/suggested_edits/{id}
Get a suggested edit object.

#### Response

Returnssuggested editobject.

### Update a suggested edit

> Update suggested edit object1500
Update suggested edit object1500

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"annotation": "https://<example>.rossum.app/api/v1/annotations/1500", "documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/123"}]}]}'\'https://<example>.rossum.app/api/v1/suggested_edits/1500'
```


```
{"id":1500,"url":"https://<example>.rossum.app/api/v1/suggested_edits/1500","annotation":"https://<example>.rossum.app/api/v1/annotations/1500","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/123"}],"target_queue":"https://<example>.rossum.app/api/v1/queues/123","values":{}}]}
```

PUT /v1/suggested_edits/{id}
Update suggested edit object.

#### Response

Returns updatedsuggested editobject.

### Update part of a suggested edit

> Update documents on suggested edit object1500
Update documents on suggested edit object1500

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"documents": [{"pages": [{"page": "https://<example>.rossum.app/api/v1/pages/123"}]}]}'\'https://<example>.rossum.app/api/v1/suggested_edits/1500'
```


```
{"id":1500,"url":"https://<example>.rossum.app/api/v1/suggested_edits/1500","annotation":"https://<example>.rossum.app/api/v1/annotations/1500","documents":[{"pages":[{"page":"https://<example>.rossum.app/api/v1/pages/123"}],"target_queue":"https://<example>.rossum.app/api/v1/queues/123","values":{}}]}
```

PATCH /v1/suggested_edits/{id}
Update part of suggested edit object.

#### Response

Returns updatedsuggested editobject.

### Delete a suggested edit

> Delete suggested edit1500
Delete suggested edit1500

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/suggested_edits/1500'
```

DELETE /v1/suggested_edits/{id}
Delete suggested edit object.

#### Response


## Survey

> Example survey object
Example survey object

```
{"id":456,"url":"https://<example>.rossum.app/api/v1/surveys/456","organization":"https://<example>.rossum.app/api/v1/organizations/42","created_at":"2019-10-13T23:04:00.933658Z","modifier":"https://<example>.rossum.app/api/v1/users/100","modified_by":"https://<example>.rossum.app/api/v1/users/100","modified_at":"2019-11-13T23:04:00.933658Z","additional_data":{},"template":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","answers":[{"value":5,"question":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a"}]}
```

A Survey object represents a collection of answers and metadata related to the survey.

Attribute | Type | Default | Description | Read-only | Required
--- | --- | --- | --- | --- | ---
id | integer |  | Id of the survey | true | 
url | URL |  | URL of the survey | true | 
organization | URL |  | Related organization | true | 
template | URL |  | Related survey template | true | 
created_at | datetime |  | Timestamp of object's creation. | true | 
modifier | URL |  | User that last modified the annotation. | true | 
modified_by | URL |  | User that last modified the annotation. | true | 
modified_at | datetime |  | Timestamp of last modification. | true | 
additional_data | object | {} | Client data. |  | 
answers | list[object] |  | Answers, linked to the questions. The number of the answers can't be changed. Seeanswers |  | true


#### Answer


Attribute | Type | Description | Read-only
--- | --- | --- | ---
value | JSON | Value of the answer. The structure depends onquestion.answer_type. Seeanswer type | 
question | URL | URL of the question | true


#### Answer type


Type | Description
--- | ---
scale | Integer. Has to be in range 1-5.
text | String. Has to be at most 250 characters long.
bool | Boolean. Default isnull.


### List all surveys

> List all surveys

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/surveys'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":234,"url":"https://<example>.rossum.app/api/v1/surveys/234",...}]}
```

Retrieve all survey objects.
Supported filters:id,template_uuidSupported ordering:id,modified_at
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofsurveyobjects.

### Create new survey object

> Create new survey from template
Create new survey from template

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"uuid": "4d73ac4b-bd1a-4b6d-b274-4e976a382b5b"}'\'https://<example>.rossum.app/api/v1/surveys/from_template'
```


```
{"id":234,"url":"https://<example>.rossum.app/api/v1/surveys/234","template":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","answers":[{"value":null,"question":"https://<example>.rossum.app/api/v1/questions/9e87fcf2-f571-4691-8850-77f813d6861a"}],...}
```

POST /v1/surveys/from_template
Create new survey object. Will have all answers pre-filled withnullanswers.

#### Response

Returns newsurveyobject.

### Retrieve a survey object

> Get survey object1234
Get survey object1234

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/surveys/1234'
```


```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/surveys/1234",...}
```


#### Response


### Update a survey

> Update survey object1234
Update survey object1234

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"additional_data": {"data": "some data"}, "answers": [{"value": 5}, {"value": 3}]}'\'https://<example>.rossum.app/api/v1/surveys/1234'
```


```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/surveys/1234",...}
```

Update survey object.

#### Response

Returns updatedsurveyobject.

### Update part of a survey

> Update subject of survey object1234
Update subject of survey object1234

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"additional_data": {"data": "some data"}, "answers": [{}, {"value": 3}, {}]}'\'https://<example>.rossum.app/api/v1/surveys/1234'
```


```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/surveys/1234",...}
```

PATCH /v1/surveys/{id}
Update part of a survey object. Empty answer object will not update contents of that answer.

#### Response

Returns updatedsurveyobject.

### Delete a survey

> Delete survey object1234
Delete survey object1234

```
curl-XDELETE'https://<example>.rossum.app/api/v1/surveys/1234'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
```

DELETE /v1/surveys/{id}
Delete a survey object.

#### Response


## Survey template

> Example survey template object
Example survey template object

```
{"url":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","uuid":"4d73ac4b-bd1a-4b6d-b274-4e976a382b5b","name":"Satisfaction survey","questions":[{"uuid":"9e87fcf2-f571-4691-8850-77f813d6861a","text":"How satisfied are you?","answer_type":"scale"}]}
```

A Survey template object represents a collection of questions related to asurvey.

Attribute | Type | Description
--- | --- | ---
uuid | string | UUID of the survey template
url | URL | URL of the survey template
name | string | Name of the survey template
questions | list[object] | list of question objects


### List all survey templates

> List all survey templates
List all survey templates

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/survey_templates'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"url":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b",...}]}
```

GET /v1/survey_templates
Retrieve all survey template objects.

#### Response

Returnspaginatedresponse with a list ofsurvey templateobjects.

### Retrieve a survey template

> Get survey template object4d73ac4b-bd1a-4b6d-b274-4e976a382b5b
Get survey template object4d73ac4b-bd1a-4b6d-b274-4e976a382b5b

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b'
```


```
{"url":"https://<example>.rossum.app/api/v1/survey_templates/4d73ac4b-bd1a-4b6d-b274-4e976a382b5b",...}
```

GET /v1/survey_templates/{uuid}
Get a survey template object.

#### Response

Returnssurvey templateobject.

## Task

> Example task object

```
{"id":1,"url":"https://<example>.rossum.app/api/v1/tasks/1","type":"documents_download","status":"succeeded","expires_at":"2021-09-11T09:59:00.000000Z","detail":null,"content":{"file_name":"my-archive.zip"},"result_url":"https://<example>.rossum.app/api/v1/documents/downloads/1"}
```

Tasks are used as status monitors of asynchronous operations.
Tasks withsucceededstatus can redirect to the object created as a result of them. Ifno_redirect=trueis passed
as a query parameter, endpoint won't redirect to an object created, but will return information about the task itself instead.

Attribute | Type | Optional | Description
--- | --- | --- | ---
id | integer |  | Task object ID.
url | URL |  | Task object URL.
type | enum |  | Currently supported options for task types aredocuments_download,upload_created, andemail_imported.
status | enum |  | One ofrunning,succeededorfailed.
expires_at | datetime |  | Timestamp of a guaranteed availability of the task object. Expired tasks are being deleted periodically.
detail | string |  | Detailed message on the status of the task. For failed tasks, error id is included in the message and can be used in communication with Rossum support for further investigation.
content | object |  | Detailed information related to tasks (seetasks contentdetail).
code | string | true | Error code.
result_url | string | true | Succeeded status resulting redirect URL.


#### Tasks content

Contains detailed information related to tasks.

Attribute | Type | Optional | Description
--- | --- | --- | ---
file_name | string |  | File name of the archive to be downloaded specified when creating adownload.


Attribute | Type | Description
--- | --- | ---
upload | url | URL of the object representing theupload.


### Retrieve task

> Get task24

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/tasks/24'
```


```
{"id":24,"url":"https://<example>.rossum.app/api/v1/tasks/24","type":"documents_download","status":"running","expires_at":"2021-09-11T09:59:00.000000Z","detail":null,"content":{"file_name":"my-archive.zip"}}
```


#### Response

If the task has status other thansucceeded, the endpoint returns status200.
If the task has statussucceeded, the endpoint redirects with status303to the newly created object.
Ifno_redirectflag was passed, the endpoint returns the task object and status200.

## Trigger

> Example trigger object
Example trigger object

```
{"id":234,"url":"https://<example>.rossum.app/api/v1/triggers/234","queue":"https://<example>.rossum.app/api/v1/queues/4321","event":"annotation_imported","condition":{},"email_templates":["https://<example>.rossum.app/api/v1/email_templates/123","https://<example>.rossum.app/api/v1/email_templates/321"],"delete_recommendations":["https://<example>.rossum.app/api/v1/delete_recommendations/123","https://<example>.rossum.app/api/v1/delete_recommendations/321"]}
```

A Trigger object represents a condition that will trigger its related object's actions when an event occurs.

Attribute | Type | Default | Required | Description | Read-only
--- | --- | --- | --- | --- | ---
id | integer |  |  | Id of the trigger | true
url | URL |  |  | URL of the trigger | true
queue | URL |  | true | URL of the associated queue | 
event | string |  | true | Event that will trigger the trigger (seetrigger event types) | 
condition | JSON | {} |  | A subset of MongoDB Query Language (seetrigger condition) | 
email_templates | list[URL] |  |  | URLs of the linked email templates | 
delete_recommendations | list[URL] |  |  | URLs of the linked delete recommendations | 

Detailed information on how to set up and use Triggers can be foundhere.

### List all triggers

> List all triggers

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/triggers'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":234,"url":"https://<example>.rossum.app/api/v1/triggers/234",...}]}
```

Retrieve all trigger objects.
Supported filters:id,event,queueSupported ordering:id,event
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list oftriggerobjects.

### Create new trigger object

> Create new trigger in queue4321
Create new trigger in queue4321

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "event": "annotation_created", "condition": {}}'\'https://<example>.rossum.app/api/v1/triggers'
```


```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/triggers/1234","queue":"https://<example>.rossum.app/api/v1/queues/4321","event":"annotation_created","condition":{}}
```

Create new trigger object.

#### Response

Returns newtriggerobject.

### Retrieve a trigger object

> Get trigger object1234
Get trigger object1234

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/triggers/1234'
```


```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/triggers/1234",...}
```

GET /v1/triggers/{id}
Get a trigger object.

#### Response

Returnstriggerobject.

### Update a trigger

> Update trigger object1234
Update trigger object1234

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"queue": "https://<example>.rossum.app/api/v1/queues/4321", "event": "annotation_created", "condition": {}}'\'https://<example>.rossum.app/api/v1/triggers/1234'
```


```
{"id":1234,"url":"https://<example>.rossum.app/api/v1/triggers/1234",...}
```

PUT /v1/triggers/{id}
Update trigger object.

#### Response

Returns updatedtriggerobject.

### Update part of a trigger

> Update subject of trigger object1234
Update subject of trigger object1234

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"event": "annotation_imported"}'\'https://<example>.rossum.app/api/v1/triggers/1234'
```


```
{"id":1234,"event":"annotation_imported",...}
```

PATCH /v1/triggers/{id}
Update part of a trigger object.

#### Response

Returns updatedtriggerobject.

### Delete a trigger

> Delete trigger object1234
Delete trigger object1234

```
curl-XDELETE'https://<example>.rossum.app/api/v1/triggers/1234'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'
```

DELETE /v1/triggers/{id}
Delete a trigger object.
Trigger ofemail_with_no_processable_attachmentseventcannot be deleted.

#### Response


## Upload

> Example upload object
Example upload object

```
{"id":314528,"url":"https://<example>.rossum.app/api/v1/uploads/314528","queue":"https://<example>.rossum.app/api/v1/queues/8199","creator":"https://<example>.rossum.app/api/v1/users/1","created_at":"2021-04-26T10:08:03.856648Z","email":"https://<example>.rossum.app/api/v1/emails/96743","organization":"https://<example>.rossum.app/api/v1/organizations/1","documents":["https://<example>.rossum.app/api/v1/documents/254322","https://<example>.rossum.app/api/v1/documents/254323"],"additional_documents":["https://<example>.rossum.app/api/v1/documents/254324"],"annotations":["https://<example>.rossum.app/api/v1/annotations/104322","https://<example>.rossum.app/api/v1/annotations/104323","https://<example>.rossum.app/api/v1/annotations/104324"]}
```

Object representing an upload.

Attribute | Type | Optional | Description
--- | --- | --- | ---
url | URL |  | Upload object URL.
queue | URL |  | URL of the target queue of the upload.
email | URL | true | URL of the email that created the upload object (if applicable).
organization | URL |  | URL of related organization
creator | URL |  | URL of the user who created the upload.
created_at | datetime |  | Time of the creation of the upload.
documents | list[URL] |  | URLs of the uploaded documents.
additional_documents | list[URL] | true | URLs of additional documents created inupload.createdevent hooks.
annotations | list[URL] | true | URLs of all created annotations.


### Create upload

> Upload file using a form (multipart/form-data)
Upload file using a form (multipart/form-data)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

> Upload file in a request body
Upload file in a request body

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

> Upload file in a request body (UTF-8 filename must be URL encoded)
Upload file in a request body (UTF-8 filename must be URL encoded)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H"Content-Disposition: attachment; filename*=utf-8''document%20%F0%9F%8E%81.pdf"--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

> Upload file in a request body with a filename in URL (UTF-8 filename must be URL encoded)
Upload file in a request body with a filename in URL (UTF-8 filename must be URL encoded)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads/document%20%F0%9F%8E%81.pdf?queue=8236'
```

> Upload multiple files using multipart/form-data
Upload multiple files using multipart/form-data

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document1.pdf-Fcontent=@document2.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

> Upload file using basic authentication
Upload file using basic authentication

```
curl-u'east-west-trading-co@<example>.rossum.app:secret'\-Fcontent=@document.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

> Upload file with additional field values and metadata
Upload file with additional field values and metadata

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-Fcontent=@document.pdf\-Fvalues='{"upload:organization_unit":"Sales"}'\-Fmetadata='{"project":"Market ABC"}'\'https://<example>.rossum.app/api/v1/uploads?queue=8236'
```

POST /v1/uploads?queue={id}
POST /v1/uploads/{filename}?queue={id}
Uploads a document to the queue specified as query parameter (starting in theimporting state).
Multiple files upload is supported, the total size of the data uploaded may not exceed 40 MB.
UTF-8 filenames are supported, see examples.
The file can be sent as a part of multipart/form-data or, alternatively, in the
request body.
The{filename}parameter in the URL path only works when sending the file in the request body using--data-binary.
When uploading via multipart/form-data, the filename is automatically extracted from the form field and the{filename}parameter in the URL is ignored. Use theContent-Dispositionheader or specify the filename in the form field instead.
You can also specify additional properties using form field:
- metadata could be passed usingmetadataform field. Metadata will
be set to newly created annotation object.
- values could be passed usingvaluesform field. It may
be used to initialize datapoint values by setting the value ofrir_field_namesin the schema.
For exampleupload:organization_unitfield may be referenced in a schema like this:{
     "category": "datapoint",
     "id": "organization_unit",
     "label": "Org unit",
     "type": "string",
     "rir_field_names": ["upload:organization_unit"]
     ...
   }

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
> Fail upload if a document with identical content andoriginal_file_namealready exists.
Fail upload if a document with identical content andoriginal_file_namealready exists.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-H'Content-Disposition: attachment; filename=document.pdf'--data-binary@file.pdf\'https://<example>.rossum.app/api/v1/uploads?queue=8236&reject_identical=true'
```

Additional arguments may be specified to prevent reupload of identical documents.
This is useful for various services and integrations that track uploaded
documents. In case of failure or service restart, the current progress may be
lost and reupload of the previously uploaded document may happen. Usingreject_identicalargument prevents such duplicates.

Argument | Type | Default | Description
--- | --- | --- | ---
reject_identical | boolean | false | When enabled, upload checks for identical documents within a given organization. If such document is found, upload fails with status 409. The check is performed based on file name and file content. Only one file is allowed whenreject_identicalis set totrue.


#### Response

Create upload endpoint is asynchronous and response contains created task url. Further information about
the import status may be acquired by retrieving the upload object or the task (for more information, please refer totask)
Example import response

```
{
  "url": "https://example.rossum.app/api/v1/tasks/315509"
}
```


### Retrieve upload

> Get upload314528

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/uploads/314528'
```


```
{"id":314528,"url":"https://<example>.rossum.app/api/v1/uploads/314528","queue":"https://<example>.rossum.app/api/v1/queues/8199","creator":"https://<example>.rossum.app/api/v1/users/1","created_at":"2021-04-26T10:08:03.856648Z","email":"https://<example>.rossum.app/api/v1/emails/96743","organization":"https://<example>.rossum.app/api/v1/organizations/1","documents":["https://<example>.rossum.app/api/v1/documents/254322","https://<example>.rossum.app/api/v1/documents/254323"],"additional_documents":["https://<example>.rossum.app/api/v1/documents/254324"],"annotations":["https://<example>.rossum.app/api/v1/annotations/104322","https://<example>.rossum.app/api/v1/annotations/104323","https://<example>.rossum.app/api/v1/annotations/104324"]}
```


#### Response


## User

> Example user object

```
{"id":10775,"url":"https://<example>.rossum.app/api/v1/users/10775","first_name":"John","last_name":"Doe","email":"john-doe@east-west-trading.com","phone_number":"+1-212-456-7890","date_joined":"2018-09-19T13:44:56.000000Z","username":"john-doe@east-west-trading.com","groups":["https://<example>.rossum.app/api/v1/groups/3"],"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8199"],"is_active":true,"last_login":"2019-02-07T16:20:18.652253Z","ui_settings":{},"metadata":{},"oidc_id":null,"deleted":false}
```

A user object represents individual user of Rossum. Every user is assigned to an organization.
A user can be assigneduser roles(permission groups). User usually has only one assigned role (with the exception ofapproverrole).
User may be assigned to one or more queues and can only access annotations
from the assigned queues. This restriction is not applied to admin users, who may
access annotations from all queues.
Users cannot be deleted, but can be disabled (setis_activetofalse).
Fieldemailcannot be changed through the API (due to security reasons).
Fieldpasswordcan be set onuser creationbut cannot be changed through the API (due to security reasons).
Fieldoidc_idwill be set to User's email when transitioning tossoauthorization, if empty.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the user | true
url | URL |  | URL of the user | true
first_name | string |  | First name of the user | 
last_name | string |  | Last name of the user | 
email | string |  | Email of the user | true
phone_number | string |  | Phone number of the user | 
password | string |  | Password (not shown on API) | 
date_joined | datetime |  | Date of user join | 
username | string |  | Username of a user | 
groups | list[URL] | [] | List ofuser role(permission groups) | 
organization | URL |  | Related organization. | 
queues | list[URL] | [] | List of queues user is assigned to. | 
is_active | bool | true | Whether user is enabled or disabled | 
last_login | datetime |  | Date of last login | 
ui_settings | object | {} | User-related frontend UI settings (e.g. locales). Rossum internal. | 
metadata | object | {} | Client data. | 
oidc_id | string | null | OIDC provider id used to match Rossum user (displayed only to admin user) | 
auth_type | string | password | Authorization method, can bessoorpassword. This field can be edited only by admin. | 
deleted | bool | false | Whether a user is deleted | true


### List all users

> List all users in the organization.
List all users in the organization.

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/users'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":10775,"url":"https://<example>.rossum.app/api/v1/users/10775","first_name":"John","last_name":"Doe","email":"john-doe@east-west-trading.com","date_joined":"2018-09-19T13:44:56.000000Z","username":"john-doe@east-west-trading.com",...}]}
```

Retrieve all user objects.
Supported filters:id,organization,username,first_name,last_name,email,is_active,last_login,groups,queue,deleted
Supported ordering:id,username,first_name,last_name,email,last_login,date_joined,deleted,not_deleted
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofuserobjects.

### Create new user

> Create new user in organization406
Create new user in organization406

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406", "username": "jane@east-west-trading.com", "email": "jane@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"], "groups": ["https://<example>.rossum.app/api/v1/groups/2"]}'\'https://<example>.rossum.app/api/v1/users'
```


```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"","last_name":"","email":"jane@east-west-trading.com","date_joined":"2019-02-09T22:16:38.969904Z","username":"jane@east-west-trading.com","phone_number":null,"groups":["https://<example>.rossum.app/api/v1/groups/2"],"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8236"],"is_active":true,"last_login":null,"ui_settings":{},"metadata":{},"oidc_id":null,"deleted":false}
```

> Create a new user with password and no email (a technical user)
Create a new user with password and no email (a technical user)

```
curl-s-XPOST-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406", "username": "technical-user@east-west-trading.com", "password": "secret"}'\'https://<example>.rossum.app/api/v1/users'
```


```
{"id":10998,"url":"https://<example>.rossum.app/api/v1/users/10998","first_name":"","last_name":"","email":"","date_joined":"2020-09-25T14:30:38.969904Z","username":"technical-user@east-west-trading.com","groups":[],"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"is_active":true,"last_login":null,"ui_settings":{},"metadata":{},"oidc_id":null,"deleted":false,...}
```

Create a new user object.For security reasons, it is better to create users without a specified password.
Such users have an invalid password.
Later, they can set their password after usingreset-password endpoint.

#### Response

Returns createduserobject.

### Retrieve a user

> Get user object10997

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/users/10997'
```


```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Jane","last_name":"Bond","email":"jane@east-west-trading.com","date_joined":"2019-02-09T22:16:38.969904Z","username":"jane@east-west-trading.com",...}
```


#### Response


### Retrieve currently authorized user

> Get user object for the currently authorized user
Get user object for the currently authorized user

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/auth/user'
```


```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Jane","last_name":"Bond","email":"jane@east-west-trading.com","date_joined":"2019-02-09T22:16:38.969904Z","username":"jane@east-west-trading.com",...}
```

Get user object for the currently authorized user.

#### Response


### Update a user

> Update user object10997
Update user object10997

```
curl-s-XPUT-H'Content-Type: application/json'-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"organization": "https://<example>.rossum.app/api/v1/organizations/406", "username": "jane@east-west-trading.com", "queues": ["https://<example>.rossum.app/api/v1/queues/8236"], "groups": ["https://<example>.rossum.app/api/v1/groups/2"], "first_name": "Jane"}'\'https://<example>.rossum.app/api/v1/users/10997'
```


```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Jane","last_name":"","email":"jane@east-west-trading.com",...}
```


#### Response

Returns updateduserobject.

### Update part of a user

> Updatefirst_nameof user object10997
Updatefirst_nameof user object10997

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"first_name": "Emma"}'\'https://<example>.rossum.app/api/v1/users/10997'
```


```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997","first_name":"Emma","last_name":"",...}
```

Update part of user object.

#### Response

Returns updateduserobject.

### Deleting a user

The following endpoints provide soft-deletion - marking a user as deleted, without a possibility of reversing the deletion.
The following rules apply to user soft-deletion:
- A regular user can delete self and nobody else
- An organization admin can delete other users within the organization, including other adminsFor trial organizations, the admin deleting self actually means the whole trial organization will be deletedFor non-trial organizationThe last admin cannot be deleted via API, but must instead create a ticket with supportIf the organization has an organization group admin, the admin can delete self but the org will be preserved
- An organization group adminCannot be deleted via APICan remove any organization admin or regular user
A regular user can delete self and nobody else
An organization admin can delete other users within the organization, including other admins
- For trial organizations, the admin deleting self actually means the whole trial organization will be deleted
- For non-trial organization
- The last admin cannot be deleted via API, but must instead create a ticket with support
- If the organization has an organization group admin, the admin can delete self but the org will be preserved
An organization group admin
- Cannot be deleted via API
- Can remove any organization admin or regular user

#### Soft-deletion

> Delete user1337

```
curl-XDELETE-H'Authorization: token db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/users/1337'
```

DELETE /v1/users/{id}

#### Response


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

> Change password of user object10997
Change password of user object10997

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"new_password1": "new_password", "new_password2": "new_password", "old_password": "old_password"}'\'https://<example>.rossum.app/api/v1/auth/password/change'
```


```
{"id":10997,"url":"https://<example>.rossum.app/api/v1/users/10997",...}
```

POST /v1/auth/password/change
Change password of current user.

#### Response


#### Reset password

> Reset password of a user with emailjane@east-west-trading.com
Reset password of a user with emailjane@east-west-trading.com

```
curl-XPOST-H'Content-Type: application/json'\-d'{"email": "jane@east-west-trading.com"}'\'https://<example>.rossum.app/api/v1/auth/password/reset'
```


```
{"detail":"Password reset e-mail has been sent."}
```

POST /v1/auth/password/reset
Reset password to a users specified by their emails.
The users are sent an email with a verification URL leading to web form, where they can set their password.

#### Response


#### Password score

> Password score and suggestions from the validators.
Password score and suggestions from the validators.

```
curl-XPOST-H'Content-Type: application/json'\-d'{"password": "password_to_score"}'\'https://<example>.rossum.app/api/v1/auth/password/score'
```


```
{"score":2,"messages":["Add another word or two. Uncommon words are better."]}
```

POST /v1/auth/password/score
Score to allow users to see how strong their password is from 0 (risky password) to 4 (strong password).

Attribute | Type | Description | Required
--- | --- | --- | ---
password | string | Password to be scored | Yes
email | string | Email of the user | No
first_name | string | First name of the user | No
last_name | string | Last name of the user | No


#### Response


## User Role

> Example role object

```
{"id":3,"url":"https://<example>.rossum.app/api/v1/groups/3","name":"admin"}
```

User role is a group of permissions that are assigned to the user. Permissions
are assigned to individual operations on objects.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the user role (may differ between different organizations) | true
url | URL |  | URL of the user role | true
name | string |  | Name of the user role | true

There are multiple pre-defined roles:

Role | Description
--- | ---
viewer | Read-only user, cannot change any API object. May be useful for automated data export or auditor access.
annotator | In addition to permissions of annotator_limited the user is also allowed toimport a document.
admin | User can modify API objects to set-up organization (e.g.workspaces,queues,schemas)
manager | In addition to permissions of annotator the user is also allowed to accessusage-reports.
annotator_limited | User that is allowed to change annotation and its datapoints. Note: this role is under active development and should not be used in production environment.
annotator_embedded | This role is specifically designed to be used withembedded mode. User can modify annotation and its datapoints, also has read-only permissions for objects needed for interaction on embedded validation screen.
organization_group_admin | In addition to permissions of admin the user can managemembershipsamongorganizationswithin herorganization group.Talk with a Rossum representative about enabling this feature.
approver | In addition to permission of viewer the user can also approve/reject annotations. This may be combined with other roles.Talk with a Rossum representative about enabling this feature.For more info seeworkflows.

User can only access annotations from queues it is assigned to, except foradminandorganization_group_adminroles that can access any queue.
Permissions assigned to the role cannot be changed through the API.

### List all user roles

> List all user roles (groups)
List all user roles (groups)

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/groups'
```


```
{"pagination":{"total":6,"total_pages":1,"next":null,"previous":null},"results":[{"id":1,"url":"https://<example>.rossum.app/api/v1/groups/1","name":"viewer"},{"id":2,"url":"https://<example>.rossum.app/api/v1/groups/2","name":"annotator"},{"id":3,"url":"https://<example>.rossum.app/api/v1/groups/3","name":"admin"},{"id":4,"url":"https://<example>.rossum.app/api/v1/groups/4","name":"manager"},{"id":5,"url":"https://<example>.rossum.app/api/v1/groups/5","name":"annotator_limited"},{"id":6,"url":"https://<example>.rossum.app/api/v1/groups/6","name":"organization_group_admin"},{"id":7,"url":"https://<example>.rossum.app/api/v1/groups/7","name":"approver"}]}
```

Retrieve all group objects.
Supported filters:name
Supported ordering:name
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofgroupobjects.

### Retrieve a user role

> Get group object2

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/groups/2'
```


```
{"url":"https://<example>.rossum.app/api/v1/groups/2","name":"annotator"}
```

Get a user role object.

#### Response


## Workflow

> Example workflow object
Example workflow object

```
{"id":7540,"name":"Approval workflow for US entity","url":"https://<example>.rossum.app/api/v1/workflows/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","condition":{}}
```


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the workflow | true
name | string |  | Name of the workflow | 
url | URL |  | URL of the workflow | true
organization | URL |  | URL of the organization | 
condition | JSON |  | Condition that designates whether the workflow will be entered | 


### List all workflows

> List all workflows

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflows'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"name":"Approval workflow for US entity","url":"https://<example>.rossum.app/api/v1/workflows/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","condition":{}}]}
```

Retrieve all workflow objects.
Supported filters:id,queue
Supported ordering:id
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofworkflowobjects.

### Retrieve a workflow

> Get workflow object7694
Get workflow object7694

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflows/7694'
```


```
{"id":7540,"name":"Approval workflow for US entity","url":"https://<example>.rossum.app/api/v1/workflows/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","condition":{}}
```

GET /v1/workflows/{id}
Get a workflow object.

#### Response

Returnsworkflowobject.

## Workflow activity

> Example workflow activity object
Example workflow activity object

```
{"id":7540,"url":"https://<example>.rossum.app/api/v1/workflow_activities/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","created_by":null,"created_at":"2021-04-26T10:08:03.856648Z","annotation":"https://<example>.rossum.app/api/v1/annotations/406101","workflow":"https://<example>.rossum.app/api/v1/workflows/7540","workflow_step":"https://<example>.rossum.app/api/v1/workflow_steps/75","workflow_run":"https://<example>.rossum.app/api/v1/workflow_runs/7512","assignees":["https://<example>.rossum.app/api/v1/users/1","https://<example>.rossum.app/api/v1/users/2"],"action":"step_started","note":"The workflow step started"}
```


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the workflow activity | true
url | URL |  | URL of the workflow activity | true
organization | URL |  | URL of the organization | true
annotation | URL |  | URL of the related annotation | true
workflow | URL |  | URL of the related workflow | true
workflow step | URL |  | URL of the related workflow step | true
workflow run | URL |  | URL of the related workflow run | true
assignees | list[URL] |  | List of all assignedusers | true
action | string |  | Supported values arestep_started,step_completed,approved,rejected,workflow_started,workflow_completed,reassigned | true
note | string |  | String note of the activity | true
created_at | datetime |  | Date and time of when the activity was created | true
created_by | URL | null | Userwho created the activity | true


### List all workflow activities

> List all workflow activities
List all workflow activities

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_activities'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"url":"https://<example>.rossum.app/api/v1/workflow_activities/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406",...}]}
```

GET /v1/workflow_activities
Retrieve all workflow activity objects.
Supported filters:id,annotation,workflow_run,created_at_before,created_at_after,assignees,action
Supported ordering:id
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofworkflow activityobjects.

### Retrieve a workflow activity

> Get workflow activity object7694
Get workflow activity object7694

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_activities/7540'
```


```
{"id":7540,"url":"https://<example>.rossum.app/api/v1/workflow_activities/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406",...}
```

GET /v1/workflow_activities/{id}
Get a workflow activity object.

#### Response

Returnsworkflow activityobject.

## Workflow run

> Example workflow run object
Example workflow run object

```
{"id":75402,"url":"https://<example>.rossum.app/api/v1/workflow_runs/75402","organization":"https://<example>.rossum.app/api/v1/organizations/406","annotation":"https://<example>.rossum.app/api/v1/annotations/7568","current_step":"https://<example>.rossum.app/api/v1/workflow_steps/7540","workflow_status":"pending"}
```


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the workflow run | true
url | URL |  | URL of the workflow run | true
organization | URL |  | URL of the organization | true
annotation | URL |  | URL of the annotation | true
current_step | URL |  | URL of the workflow step | true
workflow_status | string | pending | Status of the workflow run (supported values:pending,approved,rejected) | true


### List all workflow runs

> List all workflow runs
List all workflow runs

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_runs'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":75402,"url":"https://<example>.rossum.app/api/v1/workflow_runs/75402",...}]}
```

GET /v1/workflow_runs
Retrieve all workflow run objects.
Supported filters:id,annotation,current_step,workflow_status
Supported ordering:id
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofworkflow runsobjects.

### Retrieve a workflow run

> Get workflow run object75402
Get workflow run object75402

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_runs/75402'
```


```
{"id":75402,"url":"https://<example>.rossum.app/api/v1/workflow_runs/75402",...}
```

GET /v1/workflow_runs/{id}
Get a workflow run object.

#### Response

Returnsworkflow runobject.

### Reset workflow run

> Reset workflow run of ID319668
Reset workflow run of ID319668

```
curl-XPOST-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\-d'{"note_content": "Resetting due to invalid due date."}'\'https://<example>.rossum.app/api/v1/workflow_runs/319668/reset'
```

POST /v1/workflow_runs/{id}/reset
Resetting the workflow run leads to
- change its workflow status toin_review
- empty annotation'sassignees
- set the annotation status toto_review
- createworkflow activityof actionpushed_back

Key | Description | Required | Default
--- | --- | --- | ---
note_content | String note | No | ""


#### Response


Key | Type | Description
--- | --- | ---
annotation_status | string | New status of the annotation (to_review).
workflow_status | string | New workflow status (in_review).


## Workflow step

> Example workflow step object
Example workflow step object

```
{"id":7540,"name":"Team Lead approval step","url":"https://<example>.rossum.app/api/v1/workflow_steps/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","workflow":"https://<example>.rossum.app/api/v1/workflows/75","condition":{},"type":"approval","mode":"all","ordering":1}
```


Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the workflow step | true
name | string |  | Name of the workflow step | 
url | URL |  | URL of the workflow step | true
organization | URL |  | URL of the organization | 
workflow | URL |  | URL of the workflow | 
condition | JSON |  | Condition that designates whether the workflow step will be entered | 
type | string | approval | Type of the workflow step (currently the only supported value isapproval) | 
mode | string |  | Supported values:any- approval of one assignee is enough,all- all assignees must approve,auto- automatically approved if the condition matches. | 
ordering | integer |  | Designates the evaluation order of steps within a workflow (must be unique per a workflow) | 


### List all workflow steps

> List all workflow steps
List all workflow steps

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_Steps'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"name":"Team Lead approval step","url":"https://<example>.rossum.app/api/v1/workflow_steps/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","workflow":"https://<example>.rossum.app/api/v1/workflows/75","condition":{},"type":"approval","mode":"all","ordering":1}]}
```

GET /v1/workflow_steps
Retrieve all workflow step objects.
Supported filters:id,workflow,mode,type
Supported ordering:id
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofworkflow stepsobjects.

### Retrieve a workflow step

> Get workflow step object7694
Get workflow step object7694

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workflow_steps/7694'
```


```
{"id":7540,"name":"Team Lead approval step","url":"https://<example>.rossum.app/api/v1/workflow_steps/7540","organization":"https://<example>.rossum.app/api/v1/organizations/406","workflow":"https://<example>.rossum.app/api/v1/workflows/75","condition":{},"type":"approval","mode":"all","ordering":1}
```

GET /v1/workflow_steps/{id}
Get a workflow step object.

#### Response

Returnsworkflow stepobject.

## Workspace

> Example workspace object
Example workspace object

```
{"id":7540,"name":"East West Trading Co","url":"https://<example>.rossum.app/api/v1/workspaces/7540","autopilot":true,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8236"],"metadata":{}}
```

A workspace object is a container ofqueueobjects.

Attribute | Type | Default | Description | Read-only
--- | --- | --- | --- | ---
id | integer |  | Id of the workspace | true
name | string |  | Name of the workspace | 
url | URL |  | URL of the workspace | true
autopilot | bool |  | (Deprecated) Whether to automatically confirm datapoints (hide eyes) from previously seen annotations | true
organization | URL |  | Related organization | 
queues | list[URL] | [] | List of queues that belongs to the workspace | true
metadata | object | {} | Client data. | 


### List all workspaces

> List all workspaces

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workspaces'
```


```
{"pagination":{"total":1,"total_pages":1,"next":null,"previous":null},"results":[{"id":7540,"name":"East West Trading Co","url":"https://<example>.rossum.app/api/v1/workspaces/7540","autopilot":true,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":["https://<example>.rossum.app/api/v1/queues/8199","https://<example>.rossum.app/api/v1/queues/8236"],"metadata":{}}]}
```

Retrieve all workspace objects.
Supported filters:id,name,organization
Supported ordering:id,name
For additional info please refer tofilters and ordering.

#### Response

Returnspaginatedresponse with a list ofworkspaceobjects.

### Create a new workspace

> Create new workspace in organization406namedTest Workspace
Create new workspace in organization406namedTest Workspace

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Test Workspace", "organization": "https://<example>.rossum.app/api/v1/organizations/406"}'\'https://<example>.rossum.app/api/v1/workspaces'
```


```
{"id":7694,"name":"Test Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
```

Create a new workspace object.

#### Response

Returns createdworkspaceobject.

### Retrieve a workspace

> Get workspace object7694
Get workspace object7694

```
curl-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workspaces/7694'
```


```
{"id":7694,"name":"Test Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
```

GET /v1/workspaces/{id}
Get an workspace object.

#### Response

Returnsworkspaceobject.

### Update a workspace

> Update workspace object7694
Update workspace object7694

```
curl-XPUT-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "My Workspace", "organization": "https://<example>.rossum.app/api/v1/organizations/406"}'\'https://<example>.rossum.app/api/v1/workspaces/7694'
```


```
{"id":7694,"name":"My Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
```

PUT /v1/workspaces/{id}
Update workspace object.

#### Response

Returns updatedworkspaceobject.

### Update part of a workspace

> Update name of workspace object7694
Update name of workspace object7694

```
curl-XPATCH-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'-H'Content-Type: application/json'\-d'{"name": "Important Workspace"}'\'https://<example>.rossum.app/api/v1/workspaces/7694'
```


```
{"id":7694,"name":"Important Workspace","url":"https://<example>.rossum.app/api/v1/workspaces/7694","autopilot":false,"organization":"https://<example>.rossum.app/api/v1/organizations/406","queues":[],"metadata":{}}
```

PATCH /v1/workspaces/{id}
Update part of workspace object.

#### Response

Returns updatedworkspaceobject.

### Delete a workspace

> Delete workspace7694

```
curl-XDELETE-H'Authorization: Bearer db313f24f5738c8e04635e036ec8a45cdd6d6b03'\'https://<example>.rossum.app/api/v1/workspaces/7694'
```

DELETE /v1/workspaces/{id}
Delete workspace object.

#### Response

Status:204in case of success.409in case the workspace contains queues

## POST fails with HTTP status 500

Please check that Content-Type header in the HTTP request is set correctly
(e.g.application/json).
We will improve content type checking in the future , so that  to
return 400.

## SSL connection errors

Rossum API only supports TLS 1.2 to ensure thatup-to-date algorithms and ciphersare used.
Older SSL libraries may not work properly with TLS 1.2. If you encounter
SSL/TLS compatibility issue, please make sure the library supports TLS 1.2 and
the support is switched on.
