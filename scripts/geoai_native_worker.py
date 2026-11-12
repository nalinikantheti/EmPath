"""Persistent native-Apple-Silicon inference worker; JSON lines in/out."""
import sys,json
from pathlib import Path
import numpy as np
import torch
from transformers import AutoImageProcessor,SegformerForSemanticSegmentation
root=Path(__file__).resolve().parents[1]
cache=root/'data/models/restor-tcd-b0'
processor=AutoImageProcessor.from_pretrained(cache)
model=SegformerForSemanticSegmentation.from_pretrained(cache).eval()
device='mps' if torch.backends.mps.is_available() else 'cpu'
model.to(device);torch.set_num_threads(4)
print(json.dumps({'ready':True,'device':device,'torch':torch.__version__}),flush=True)
for line in sys.stdin:
 try:
  task=json.loads(line)
  rgb=np.load(task['input'])
  inputs=processor(images=rgb,return_tensors='pt',do_resize=False).to(device)
  with torch.inference_mode():
   logits=model(**inputs).logits
   logits=torch.nn.functional.interpolate(logits,size=rgb.shape[:2],mode='bilinear',align_corners=False)
   prob=logits.softmax(dim=1)[0,1].cpu().numpy()
  if not np.isfinite(prob).all():raise ValueError('Non-finite model output')
  result=np.stack([(prob>=.5).astype('uint8'),np.round(prob*100).astype('uint8')])
  np.save(task['output'],result)
  print(json.dumps({'ok':True}),flush=True)
 except Exception as e:print(json.dumps({'ok':False,'error':str(e)}),flush=True)
