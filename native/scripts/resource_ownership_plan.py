"""Complete native/WASM/browser jobs; reuse the single compiled core."""
import os
def core_python_contracts(python,count):
    return ['env',f'NOCTURNE_RESOURCE_OWNERSHIP_SHARD=0/{count}',python,'-m','unittest','discover','-s','tests','-v']

def ownership_jobs(python,count):
    jobs=[('resource-ownership-bytes',['node','tests/resource_ownership_bytes.test.mjs'])]
    for index in range(count):
        selection=f'{index}/{count}'
        if index:
            jobs.append((f'resource-ownership-native-{index}-of-{count}',
                ['env','PYTHONPATH=tests'+os.pathsep+'..',f'NOCTURNE_RESOURCE_OWNERSHIP_SHARD={selection}',python,'-m','unittest','-v',
                    'test_resource_ownership_gallery.ResourceOwnershipGallery.test_unbound_attach_detach_and_replay_match_full_public_source']))
        jobs.append((f'resource-ownership-wasm-{index}-of-{count}',
            ['node','bindings/typescript/resource-ownership-gallery.test.mjs',selection,f'evidence/resource-ownership-wasm-{index}-of-{count}.json']))
        jobs.append((f'resource-ownership-browser-{index}-of-{count}',
            [python,'scripts/check_resource_ownership_browser.py','--shard',selection,'--output',f'evidence/resource-ownership-browser-{index}-of-{count}.json']))
    return jobs
