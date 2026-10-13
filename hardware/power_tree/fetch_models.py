from pathlib import Path
from zipfile import ZipFile
from urllib.request import urlopen
import hashlib,json
p=Path(__file__).resolve().parent/'vendor';p.mkdir(exist_ok=True)
manifest=[]
expected={'SLVM893':'0e66ec33e5d44c0358abef9c1e6d74289679799d6338f35da16457418457bf09','SLVM436':'2e2e8abe16d4edfb3712487cc78baf418510928e7358470b7c1517637ef5caca','SLVM936':'a82d230643a20a3d6a5a5d2ee53564d55b8c5b2092b15fbf584638dde9e832d2'}
for name,member,out in [('SLVM436','TPS62130_PSPICE_TRANS/tps62130_trans.lib','tps62130_trans.lib'),('SLVM936','TPS62130_PSPICE_AVG/TPS62130_AVG.lib','tps62130_avg.lib'),('SLVM893','TPS62130A_PSPICE_TRANS/TPS62130A_TRANS.LIB','tps62130a_trans.lib')]:
    url=f'https://www.ti.com/lit/zip/{name}'
    archive=p/f'{name}.zip'
    if not archive.exists(): archive.write_bytes(urlopen(url,timeout=60).read())
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected[name], 'TI model archive changed; review before reuse'
    with ZipFile(archive) as z: (p/out).write_bytes(z.read(member))
    manifest.append(dict(url=url,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),member=member))
(p.parent/'vendor-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
