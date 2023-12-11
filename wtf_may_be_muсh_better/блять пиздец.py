def extract_json_filed_data(specification, obj, spec_id, subdomain, is_element=False) -> str:
    if not (json_fields := obj.json_fields):
        return ""
    if isinstance(json_fields, str):
        json_fields = json.loads(json_fields)

    if type(json_fields) is dict:
        if not (json_field := json_fields.get(spec_id)):
            return ""

    if type(json_fields) is list:
        json_field = next(iter([jf for jf in json_fields if 'key' in jf and jf['key'] == spec_id and 'values' in jf]), None)
        if not json_field:
            return ""

    if specification[TYPE] == ProcessedReportFormFieldSpecTypes.MEDIA:
        if is_element:
            encryption = encrypt_any_data_token({
                "instance_id": obj.processed_report.id,
                'elements': [{'id': obj.id, "json_field_ids": [spec_id]}]
            })

        else:
            encryption = encrypt_any_data_token({"instance_id": obj.id, "json_field_ids": [spec_id]})
        return make_report_public_link(quote(encryption), subdomain)

    return ", ".join(list(map(str, json_field["values"])))



"""
что это за хуйня?
    json_field = next(iter([jf for jf in json_fields if 'key' in jf and jf['key'] == spec_id and 'values' in jf]), None)
"""
json_field = next(iter([jf for jf in json_fields if 'key' in jf and jf['key'] == spec_id and 'values' in jf]), None)

check1 = "type" in jf and jf["type"] in ["cards", "loop"]
check2 = "type" in jf and jf["type"] in ["photo"] and "standalone" in jf and jf["standalone"]

if not "values" in card or card["values"] is None:
    continue
