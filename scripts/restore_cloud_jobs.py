#!/usr/bin/env python3
"""
Generate clean SQL update statement for public.sync_state.
"""
import json

def main():
    with open('data/sync_state_prepared_update.json', 'r', encoding='utf-8') as f:
        payload = json.load(f)

    # Convert to clean minified JSON
    payload_str = json.dumps(payload, ensure_ascii=False)

    sql = (
        "UPDATE public.sync_state\n"
        "SET payload = $payload$" + payload_str + "$payload$::jsonb,\n"
        "    version = version + 1,\n"
        "    updated_at = NOW()\n"
        "WHERE id = 'default';\n\n"
        "SELECT id, version, updated_at,\n"
        "       jsonb_array_length(payload->'purged') as purged_count,\n"
        "       jsonb_array_length(payload->'starred') as starred_count\n"
        "FROM public.sync_state\n"
        "WHERE id = 'default';"
    )

    with open('data/update_query.sql', 'w', encoding='utf-8') as f:
        f.write(sql)
    print("Clean SQL generated successfully. Characters:", len(sql))

if __name__ == '__main__':
    main()
