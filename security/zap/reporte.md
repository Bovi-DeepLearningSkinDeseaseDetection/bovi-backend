# ZAP Scanning Report

ZAP by [Checkmarx](https://checkmarx.com/).


## Summary of Alerts

| Risk Level | Number of Alerts |
| --- | --- |
| High | 0 |
| Medium | 0 |
| Low | 0 |
| Informational | 3 |




## Insights

| Level | Reason | Site | Description | Statistic |
| --- | --- | --- | --- | --- |
| Medium | Exceeded High | http://api:8000 | Percentage of responses with status code 4xx | 63 % |
| Low | Warning |  | ZAP warnings logged - see the zap.log file for details | 15    |
| Info | Informational | http://api:8000 | Percentage of responses with status code 2xx | 36 % |
| Info | Informational | http://api:8000 | Percentage of endpoints with content type application/json | 100 % |
| Info | Informational | http://api:8000 | Percentage of endpoints with method GET | 56 % |
| Info | Informational | http://api:8000 | Percentage of endpoints with method POST | 43 % |
| Info | Informational | http://api:8000 | Count of total endpoints | 39    |
| Info | Exceeded Low | http://api:8000 | Percentage of slow responses | 5 % |







## Alerts

| Name | Risk Level | Number of Instances |
| --- | --- | --- |
| A Client Error response code was returned by the server | Informational | 41 |
| Authentication Request Identified | Informational | 1 |
| Non-Storable Content | Informational | Systemic |




## Alert Detail



### [ A Client Error response code was returned by the server ](https://www.zaproxy.org/docs/alerts/100000/)



##### Informational (High)

### Description

A response code of 400 was returned by the server.
This may indicate that the application is failing to handle unexpected input correctly.
Raised by the 'Alert on HTTP Response Code Error' script

* URL: http://api:8000
  * Node Name: `http://api:8000`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/
  * Node Name: `http://api:8000/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/5878949370204673121
  * Node Name: `http://api:8000/5878949370204673121`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api
  * Node Name: `http://api:8000/api`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/
  * Node Name: `http://api:8000/api/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/5799628156336831701
  * Node Name: `http://api:8000/api/5799628156336831701`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1
  * Node Name: `http://api:8000/api/v1`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/
  * Node Name: `http://api:8000/api/v1/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/1018721469035482402
  * Node Name: `http://api:8000/api/v1/1018721469035482402`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/animals%3Flimit=http%253A%252F%252Fwww.google.com%252F&cursor=
  * Node Name: `http://api:8000/api/v1/animals (cursor,limit)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth
  * Node Name: `http://api:8000/api/v1/auth`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/
  * Node Name: `http://api:8000/api/v1/auth/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/8795905184657984332
  * Node Name: `http://api:8000/api/v1/auth/8795905184657984332`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/actuator/health
  * Node Name: `http://api:8000/api/v1/auth/actuator/health`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/evaluations%3Flimit=http%253A%252F%252Fwww.google.com%252F&cursor=
  * Node Name: `http://api:8000/api/v1/evaluations (cursor,limit)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: http://api:8000/api/v1/media
  * Node Name: `http://api:8000/api/v1/media`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/media/
  * Node Name: `http://api:8000/api/v1/media/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/media/5479695753310671018
  * Node Name: `http://api:8000/api/v1/media/5479695753310671018`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/sync
  * Node Name: `http://api:8000/api/v1/sync`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/sync/
  * Node Name: `http://api:8000/api/v1/sync/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/sync/7680107617874562360
  * Node Name: `http://api:8000/api/v1/sync/7680107617874562360`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/login
  * Node Name: `http://api:8000/api/v1/auth/login ()({email,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/login
  * Node Name: `http://api:8000/api/v1/auth/login ()({email,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/refresh
  * Node Name: `http://api:8000/api/v1/auth/refresh ()({refresh_token})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/refresh/
  * Node Name: `http://api:8000/api/v1/auth/refresh/ ()({refresh_token})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/register
  * Node Name: `http://api:8000/api/v1/auth/register ()({consent_accepted,email,name,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `400`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/register
  * Node Name: `http://api:8000/api/v1/auth/register ()({consent_accepted,email,name,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `409`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/register
  * Node Name: `http://api:8000/api/v1/auth/register ()({consent_accepted,email,name,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: http://api:8000/api/v1/auth/register/
  * Node Name: `http://api:8000/api/v1/auth/register/ ()({consent_accepted,email,name,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `400`
  * Other Info: ``
* URL: http://api:8000/api/v1/media/download-url
  * Node Name: `http://api:8000/api/v1/media/download-url ()({evaluation_ids:[]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: http://api:8000/api/v1/media/download-url/
  * Node Name: `http://api:8000/api/v1/media/download-url/ ()({evaluation_ids:[]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: http://api:8000/api/v1/media/upload-url
  * Node Name: `http://api:8000/api/v1/media/upload-url ()({evaluation_ids:[]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: http://api:8000/api/v1/sync/animals
  * Node Name: `http://api:8000/api/v1/sync/animals ()({animals:[{breed,created_at,ear_tag,id,sex}]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: http://api:8000/api/v1/sync/evaluations
  * Node Name: `http://api:8000/api/v1/sync/evaluations ()({evaluations:[{animal_id,body_zone,catalog_version,clinical_codes:[{code,display,system}..],confidence,evaluated_at,id,image_origin,inference_ms,model_version,outcome,predicted_class,probabilities:[{label,probability}..]}]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `422`
  * Other Info: ``
* URL: http://api:8000/computeMetadata/v1/
  * Node Name: `http://api:8000/computeMetadata/v1/ ()({email,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/latest/meta-data/
  * Node Name: `http://api:8000/latest/meta-data/ ()({email,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/metadata/instance
  * Node Name: `http://api:8000/metadata/instance ()({email,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/metadata/v1
  * Node Name: `http://api:8000/metadata/v1 ()({email,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/opc/v1/instance/
  * Node Name: `http://api:8000/opc/v1/instance/ ()({email,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/opc/v2/instance/
  * Node Name: `http://api:8000/opc/v2/instance/ ()({email,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://api:8000/openstack/latest/meta_data.json
  * Node Name: `http://api:8000/openstack/latest/meta_data.json ()({email,password})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``


Instances: 41

### Solution



### Reference



#### CWE Id: [ 388 ](https://cwe.mitre.org/data/definitions/388.html)


#### WASC Id: 20

#### Source ID: 4

### [ Authentication Request Identified ](https://www.zaproxy.org/docs/alerts/10111/)



##### Informational (High)

### Description

The given request has been identified as an authentication request. The 'Other Info' field contains a set of key=value lines which identify any relevant fields. If the request is in a context which has an Authentication Method set to "Auto-Detect" then this rule will change the authentication to match the request identified.

* URL: http://api:8000/api/v1/auth/login
  * Node Name: `http://api:8000/api/v1/auth/login ()({email,password})`
  * Method: `POST`
  * Parameter: `email`
  * Attack: ``
  * Evidence: `password`
  * Other Info: `userParam=email
userValue=juan.perez@example.com
passwordParam=password`


Instances: 1

### Solution

This is an informational alert rather than a vulnerability and so there is nothing to fix.

### Reference


* [ https://www.zaproxy.org/docs/desktop/addons/authentication-helper/auth-req-id/ ](https://www.zaproxy.org/docs/desktop/addons/authentication-helper/auth-req-id/)



#### Source ID: 3

### [ Non-Storable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are not storable by caching components such as proxy servers. If the response does not contain sensitive, personal or user-specific information, it may benefit from being stored and cached, to improve performance.

* URL: http://api:8000/api/v1/animals%3Flimit=50&cursor=
  * Node Name: `http://api:8000/api/v1/animals (cursor,limit)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `no-store`
  * Other Info: ``
* URL: http://api:8000/api/v1/evaluations%3Flimit=50&cursor=
  * Node Name: `http://api:8000/api/v1/evaluations (cursor,limit)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `no-store`
  * Other Info: ``
* URL: http://api:8000/api/v1/media/download-url
  * Node Name: `http://api:8000/api/v1/media/download-url ()({evaluation_ids:[]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `no-store`
  * Other Info: ``
* URL: http://api:8000/api/v1/media/upload-url
  * Node Name: `http://api:8000/api/v1/media/upload-url ()({evaluation_ids:[]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `no-store`
  * Other Info: ``
* URL: http://api:8000/api/v1/sync/animals
  * Node Name: `http://api:8000/api/v1/sync/animals ()({animals:[{breed,created_at,ear_tag,id,sex}]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `no-store`
  * Other Info: ``

Instances: Systemic


### Solution

The content may be marked as storable by ensuring that the following conditions are satisfied:
The request method must be understood by the cache and defined as being cacheable ("GET", "HEAD", and "POST" are currently defined as cacheable)
The response status code must be understood by the cache (one of the 1XX, 2XX, 3XX, 4XX, or 5XX response classes are generally understood)
The "no-store" cache directive must not appear in the request or response header fields
For caching by "shared" caches such as "proxy" caches, the "private" response directive must not appear in the response
For caching by "shared" caches such as "proxy" caches, the "Authorization" header field must not appear in the request, unless the response explicitly allows it (using one of the "must-revalidate", "public", or "s-maxage" Cache-Control response directives)
In addition to the conditions above, at least one of the following conditions must also be satisfied by the response:
It must contain an "Expires" header field
It must contain a "max-age" response directive
For "shared" caches such as "proxy" caches, it must contain a "s-maxage" response directive
It must contain a "Cache Control Extension" that allows it to be cached
It must have a status code that is defined as cacheable by default (200, 203, 204, 206, 300, 301, 404, 405, 410, 414, 501).

### Reference


* [ https://datatracker.ietf.org/doc/html/rfc7234 ](https://datatracker.ietf.org/doc/html/rfc7234)
* [ https://datatracker.ietf.org/doc/html/rfc7231 ](https://datatracker.ietf.org/doc/html/rfc7231)
* [ https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html ](https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html)


#### CWE Id: [ 524 ](https://cwe.mitre.org/data/definitions/524.html)


#### WASC Id: 13

#### Source ID: 3


