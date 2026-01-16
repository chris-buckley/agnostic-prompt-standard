<constants>
// Example: multi-line JSON constant using JSON<< ... >>.
// Engines parse BODY as JsonValue then compile it to canonical JSON (see json_spacing).

DEFAULT_TZ: "Z"

API_CONFIG: JSON<<
{
  "apiBasePath": "/v1",
  "defaultTimeZone": DEFAULT_TZ,
  "retries": 3,
  "timeoutMs": 2000
}
>>
</constants>
