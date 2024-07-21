# ALTYS
Altys Assignment


CURL TO ACCESS THE API

curl --location 'http://127.0.0.1:5000/scrape' \
--header 'x-access-token: Navdeep' \
--header 'Content-Type: application/json' \
--header 'Cookie: csrftoken=zAFB0YDFCyjYegiYGOkt5PcMBZfqvGFI' \
--data '{
  "pages_limit": 1
}'
