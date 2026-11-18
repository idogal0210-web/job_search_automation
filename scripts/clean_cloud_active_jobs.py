#!/usr/bin/env python3
"""
Clean active jobs and their keys from public.sync_state in Supabase.
Safely preserves all user starred jobs and historical purged records.
"""
import json
import re
import urllib.request

def get_canonical(link):
    if not link:
        return ''
    m = re.search(r'linkedin\.com/jobs/view/.*?(\d{8,})', link)
    if m:
        return f'li_{m.group(1)}'
    m = re.search(r'drushim\.co\.il/job/(\d+)', link)
    if m:
        return f'drushim_{m.group(1)}'
    m = re.search(r'comeet\.com/jobs/[^/]+/[^/]+/[^/]+/([^/?#]+)', link)
    if m:
        return f'comeet_{m.group(1)}'
    m = re.search(r'jobs\.lever\.co/[^/]+/([a-f0-9-]+)', link)
    if m:
        return f'lever_{m.group(1)}'
    m = re.search(r'boards\.greenhouse\.io/[^/]+/jobs/(\d+)', link)
    if m:
        return f'greenhouse_{m.group(1)}'
    return ''

def main():
    with open('docs/data/jobs.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    jobs = d.get('jobs', []) if isinstance(d, dict) else d

    active_keys = set()
    for j in jobs:
        for k in ['link', 'stable_job_id', 'content_hash']:
            v = j.get(k)
            if v:
                v_str = str(v).strip()
                active_keys.add(v_str)
                active_keys.add(v_str.rstrip('/'))
                active_keys.add(v_str.rstrip('/') + '/')
                active_keys.add(v_str.lower())
        c = get_canonical(j.get('link', ''))
        if c:
            active_keys.add(c)
            active_keys.add(c.lower())

    print(f'Total active jobs: {len(jobs)}')
    print(f'Total active keys identified: {len(active_keys)}')

    # Fetch current row from Supabase via anon key or local snapshot
    # We can prepare the SQL update script directly.
    # Let us read the raw JSON from step 2193
    with open('/Users/ido/.gemini/antigravity/brain/1caedfbb-36ca-40b0-95bc-5fad2e798a3c/.system_generated/steps/2193/output.txt') as f:
        raw = json.load(f)
    res = raw['result']
    s = res[res.find('[{'):res.rfind('}]') + 2]
    data = json.loads(s)
    payload = json.loads(data[0]['jsonb_pretty'])

    orig_purged = payload.get('purged', [])
    clean_purged = [k for k in orig_purged if k not in active_keys]
    print(f'Purged before: {len(orig_purged)}, Purged after: {len(clean_purged)}')
    print(f'Removed keys from purged: {len(orig_purged) - len(clean_purged)}')

    clean_payload = {
        'saved': payload.get('saved', []),
        'starred': payload.get('starred', []),
        'rejected': [k for k in payload.get('rejected', []) if k not in active_keys],
        'purged': clean_purged,
        'updated_at': '2026-11-18T21:30:00.000Z'
    }

    payload_json = json.dumps(clean_payload, ensure_ascii=False)

    sql = (
        "UPDATE public.sync_state\n"
        "SET payload = $payload$" + payload_json + "$payload$::jsonb,\n"
        "    version = 20,\n"
        "    updated_at = NOW()\n"
        "WHERE id = 'default';\n\n"
        "SELECT id, version, updated_at,\n"
        "       jsonb_array_length(payload->'purged') as purged_count,\n"
        "       jsonb_array_length(payload->'starred') as starred_count,\n"
        "       jsonb_array_length(payload->'saved') as saved_count,\n"
        "       jsonb_array_length(payload->'rejected') as rejected_count\n"
        "FROM public.sync_state\n"
        "WHERE id = 'default';"
    )

    with open('data/clean_sync_state.sql', 'w', encoding='utf-8') as f:
        f.write(sql)
    print('Generated data/clean_sync_state.sql successfully.')

if __name__ == '__main__':
    main()
