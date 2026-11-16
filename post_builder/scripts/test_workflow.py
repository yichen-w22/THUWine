"""Meaningful regression checks; temporary fixtures never approve a real post."""
import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
import time
import threading
from pathlib import Path
from PIL import Image, ImageChops

SCRIPT=Path(__file__).resolve().with_name('post_builder.py')
spec=importlib.util.spec_from_file_location('post_builder',SCRIPT)
pb=importlib.util.module_from_spec(spec);spec.loader.exec_module(pb)
REAL_ROOT=pb.ROOT

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.post-builder-check-',dir=REAL_ROOT)
        self.root=Path(self.temp.name).resolve()
        assert self.root.parent==REAL_ROOT.resolve()
        pb.ROOT=self.root
        (self.root/'scripts').mkdir()
        shutil.copy2(REAL_ROOT/'scripts/export_images.cjs',self.root/'scripts/export_images.cjs')
        self.theme=pb.read_json(REAL_ROOT/'theme.json')
        self.theme['export']['format']='png'
        pb.write_json(self.root/'theme.json',self.theme)
        self.project=self.root/'projects/fixture';self.project.mkdir(parents=True)
        self.post={'schema_version':1,'title':'内部回归测试','theme':self.theme['id'],'assets':{},'sources':{},'sections':[
            {'id':'first','label':'第一节','blocks':[{'id':'intro','type':'paragraph','text':'风土与葡萄酒。\n第二行检查。'}]},
            {'id':'second','label':'第二节','blocks':[{'id':'end','type':'paragraph','text':'图像连续拼接检查。'}]}]}
        self.save()
    def tearDown(self):
        pb.ROOT=REAL_ROOT;self.temp.cleanup()
    def save(self):pb.write_json(self.project/'post.json',self.post)
    def p(self):return pb.Project(self.project)
    def test_preview_has_selectable_text_and_no_image_export(self):
        p=self.p();pb.preview(p,'内部测试')
        html=(self.project/'preview/index.html').read_text(encoding='utf-8')
        self.assertIn('<text ',html)
        self.assertFalse((self.project/'exports').exists())
        self.assertFalse((self.project/'approval.json').exists())
    def test_explicit_logo_configuration_preserves_aspect(self):
        self.theme['branding']={'name':'协会','logo':{'path':'assets/thu-wine-logo.png','crop':[419,276,1130,756],'width':320}}
        pb.write_json(self.root/'theme.json',self.theme)
        (self.root/'assets').mkdir()
        Image.new('RGBA',(2004,1285),(0,0,0,0)).save(self.root/'assets/thu-wine-logo.png')
        post=pb.initial_post(self.project,'新推送')
        self.assertEqual(post['assets']['association_logo']['path'],'../../assets/thu-wine-logo.png')
        logo=post['sections'][0]['blocks'][0]
        self.assertEqual(logo['id'],'association-logo')
        for i,section in enumerate(post['sections']):
            section['blocks'].append({'id':f'text-{i}','type':'paragraph','text':'正文内容。'})
        self.post=post;self.save();pb.init_markdown(self.project,self.root)
        project=self.p();self.assertFalse(project.validate()['errors'])
        scene=pb.Layout(project).build();images=[n for n in scene['nodes'] if n['kind']=='image']
        self.assertEqual(len(images),1)
        image=images[0];self.assertEqual(image['width'],320)
        self.assertAlmostEqual(image['width']/image['height'],image['crop'][2]/image['crop'][3])
        self.assertAlmostEqual(image['x']+image['width']/2,540)
    def test_export_without_approval_is_blocked(self):
        with self.assertRaisesRegex(ValueError,'no matching approval'):pb.export(self.p())
        self.assertFalse((self.project/'exports').exists())
    def test_stale_content_cannot_be_approved_or_exported(self):
        p=self.p();pb.preview(p,'test');pb.approve(p,'内部测试fixture，非用户稿件')
        self.post['sections'][0]['blocks'][0]['text']='变化后的内容';self.save();changed=self.p()
        with self.assertRaisesRegex(ValueError,'stale'):pb.approve(changed,'test')
        with self.assertRaisesRegex(ValueError,'no matching approval'):pb.export(changed)
    def test_changed_asset_invalidates_approval(self):
        asset=self.project/'asset.png';Image.new('RGB',(2,2),'white').save(asset)
        self.post['assets']['photo']={'path':'asset.png'};self.save()
        p=self.p();pb.preview(p,'test');pb.approve(p,'内部fixture测试')
        Image.new('RGB',(2,2),'black').save(asset)
        with self.assertRaisesRegex(ValueError,'no matching approval'):pb.export(self.p())
    def test_changed_theme_invalidates_approval(self):
        p=self.p();pb.preview(p,'test');pb.approve(p,'内部fixture测试')
        self.theme['type']['body']['size']+=1;pb.write_json(self.root/'theme.json',self.theme)
        with self.assertRaisesRegex(ValueError,'no matching approval'):pb.export(self.p())
    def test_unconfirmed_notice_blocks_preview(self):
        self.post['sections'][0]['blocks'].append({'id':'policy','type':'notice','text':'费用规定','confirmed':False});self.save()
        self.assertTrue(self.p().validate()['errors'])
    def test_missing_wine_is_detected(self):
        self.post['expected_wine_count']=2
        self.post['sections'][0]['blocks'].append({'id':'wines','type':'wine_list','items':[{'name':'一款酒','description':'来源待核对'}]});self.save()
        self.assertTrue(any('Wine count' in s for s in self.p().validate()['errors']))
    def test_markdown_roundtrip_preserves_text(self):
        pb.init_markdown(self.project,self.root)
        p=self.p()
        self.assertEqual(p.post['sections'],self.post['sections'])
        self.assertEqual(p.post['title'],self.post['title'])
        raw=pb.read_json(self.project/'post.json')
        self.assertEqual(raw['sections'][0]['blocks'][0]['text'],{'$text':'intro/text'})
        self.assertTrue((self.project/'开始编辑.cmd').exists())
    def table_block(self):
        return {'id':'grid','type':'table','columns':[{'label':'编号','width':100},{'label':'采收与工艺','width':836}],
                'rows':[{'id':'wine1','cells':['#1','第一行\n第二行\n第三行']},{'id':'wine2','cells':['#2','后续行']} ]}
    def test_table_wraps_and_next_row_clears_previous_cell(self):
        block=self.table_block();block['columns'][0]['width']=180;block['columns'][1]['width']=756
        block['rows'][0]['cells'][1]='足够长的工艺说明需要自动换行。'*6
        self.post['sections'][0]['blocks']=[block];self.save()
        project=self.p();self.assertFalse(project.validate()['errors'])
        renderer=pb.Layout(project);scene=renderer.build()
        nodes=[n for n in scene['nodes'] if n['kind']=='text' and n['id'].startswith('grid-')]
        second=next(n for n in nodes if n['text']=='#2')
        first=next(n for n in nodes if n['text']=='#1')
        wrapped=[n for n in nodes if n['x']>self.theme['canvas']['margin']+180 and first['y']<=n['y']<second['y']]
        self.assertGreater(len(wrapped),1)
        self.assertGreater(second['y'],max(n['y']+n['line'] for n in wrapped))
        for n in nodes:
            cell_right=self.theme['canvas']['margin']+(180 if n['x']<self.theme['canvas']['margin']+180 else 936)-12
            self.assertLessEqual(n['x']+renderer.measure(n['text'],n['size'],n['font']),cell_right+.1)
    def test_table_markdown_edit_and_refresh_preserve_cells(self):
        block=self.table_block();self.post['sections'][0]['blocks']=[block];self.save()
        pb.init_markdown(self.project,self.root)
        raw=pb.read_json(self.project/'post.json')
        self.assertEqual(raw['sections'][0]['blocks'][0]['rows'][0]['cells'][0],{'$text':'grid/row/wine1/0'})
        md=self.project/'正文.md';md.write_text(md.read_text(encoding='utf-8').replace('第一行','修改后的第一行'),encoding='utf-8')
        raw['sections'][0]['blocks'][0]['rows'].append({'id':'wine3','cells':['#3','新增行']})
        pb.write_json(self.project/'post.json',raw);pb.init_markdown(self.project,self.root,refresh=True)
        changed=self.p();table=changed.post['sections'][0]['blocks'][0]
        self.assertIn('修改后的第一行',table['rows'][0]['cells'][1])
        self.assertEqual(table['rows'][2]['cells'][1],'新增行')
        pb.preview(changed,'表格文字校验');html=(self.project/'preview/index.html').read_text(encoding='utf-8')
        self.assertIn('修改后的第一行',html)
        self.assertFalse((self.project/'approval.json').exists())
    def test_table_rejects_mismatched_cells_and_widths(self):
        block=self.table_block();block['rows'][0]['cells'].pop();block['columns'][0]['width']=200
        self.post['sections'][0]['blocks']=[block];self.save()
        errors=self.p().validate()['errors']
        self.assertTrue(any('one text cell per column' in error for error in errors))
        self.assertTrue(any('column widths' in error for error in errors))
    def test_markdown_preserves_title_lines_and_sponsor_paragraphs(self):
        self.post['sections'][0]['blocks']=[{'id':'cover','type':'cover','brand':'署名','title_lines':['黄河北岸的','风土之旅'],'subtitle':'副标题','meta':'日期'},
            {'id':'sponsor','type':'sponsor','thanks':'场地支持','paragraphs':['第一段介绍。','第二段介绍。']}]
        self.save();pb.init_markdown(self.project,self.root)
        p=self.p();blocks=p.post['sections'][0]['blocks']
        self.assertEqual(blocks[0]['title_lines'],['黄河北岸的','风土之旅'])
        self.assertEqual(blocks[1]['paragraphs'],['第一段介绍。','第二段介绍。'])
    def test_markdown_edit_reaches_preview_and_invalidates_approval(self):
        pb.init_markdown(self.project,self.root)
        p=self.p();pb.preview(p,'test');pb.approve(p,'内部fixture测试')
        md=self.project/'正文.md'
        md.write_text(md.read_text(encoding='utf-8').replace('风土与葡萄酒。','修改后的简介。'),encoding='utf-8')
        changed=self.p();pb.preview(changed,'test')
        html=(self.project/'preview/index.html').read_text(encoding='utf-8')
        self.assertIn('修改后的简介。',html)
        with self.assertRaisesRegex(ValueError,'no matching approval'):pb.export(changed)
    def test_markdown_refresh_preserves_edits_and_adds_fields(self):
        pb.init_markdown(self.project,self.root)
        md=self.project/'正文.md';md.write_text(md.read_text(encoding='utf-8').replace('风土与葡萄酒。','用户自己改的简介。'),encoding='utf-8')
        raw=pb.read_json(self.project/'post.json');raw['sections'][0]['blocks'].append({'id':'added','type':'paragraph','text':'新增加的段落。'})
        pb.write_json(self.project/'post.json',raw);pb.init_markdown(self.project,self.root,refresh=True)
        p=self.p()
        self.assertIn('用户自己改的简介。',p.post['sections'][0]['blocks'][0]['text'])
        self.assertEqual(p.post['sections'][0]['blocks'][-1]['text'],'新增加的段落。')
    def test_bad_markdown_keeps_last_valid_page(self):
        from live_preview import Watcher
        pb.init_markdown(self.project,self.root)
        watcher=Watcher(self.project,self.root,pb.Project,pb.preview);self.assertTrue(watcher.rebuild())
        before=(self.project/'preview/index.html').read_bytes()
        md=self.project/'正文.md';md.write_text(md.read_text(encoding='utf-8')+'\n游离于编辑区域外的文字\n',encoding='utf-8')
        self.assertFalse(watcher.rebuild());self.assertTrue(watcher.snapshot()['error'])
        self.assertEqual(before,(self.project/'preview/index.html').read_bytes())
    def test_live_preview_updates_after_markdown_save(self):
        from live_preview import serve,request_status,stop_server
        import urllib.request
        pb.init_markdown(self.project,self.root)
        errors=[]
        def run():
            try:serve(self.project,self.root,pb.Project,pb.preview,port=0)
            except Exception as exc:errors.append(exc)
        thread=threading.Thread(target=run,daemon=True);thread.start()
        info=self.project/'preview/server.json'
        try:
            deadline=time.monotonic()+10
            while time.monotonic()<deadline and not info.exists() and not errors:time.sleep(.1)
            self.assertFalse(errors);self.assertTrue(info.exists())
            data=pb.read_json(info);initial=request_status(data['port'])
            md=self.project/'正文.md';md.write_text(md.read_text(encoding='utf-8').replace('风土与葡萄酒。','自动更新成功。'),encoding='utf-8')
            deadline=time.monotonic()+10;state=initial
            while time.monotonic()<deadline:
                state=request_status(data['port'])
                if state['revision']>initial['revision']:break
                time.sleep(.1)
            self.assertGreater(state['revision'],initial['revision'])
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(f'http://127.0.0.1:{data["port"]}/',timeout=3) as response:html=response.read().decode('utf-8')
            self.assertIn('自动更新成功。',html);self.assertIn('setTimeout(poll,1000)',html)
        finally:
            if info.exists():stop_server(self.project)
            thread.join(timeout=5)
        self.assertFalse(thread.is_alive());self.assertFalse(info.exists())
    def test_equal_width_exports_stitch_exactly(self):
        import subprocess
        p=self.p();pb.preview(p,'内部测试');pb.approve(p,'内部fixture验证，不是实际推送批准');pb.export(p)
        out=self.project/'exports'/p.digest[:12];manifest=pb.read_json(out/'manifest.json')
        self.assertEqual(len(manifest['images']),2)
        self.assertEqual({s['width'] for s in manifest['images']},{1080})
        self.assertEqual(sum(s['height'] for s in manifest['images']),manifest['height'])
        # Compare a stitched lossless export with the same complete canvas, detecting gaps/repeated rows.
        full=self.root/'complete.png'
        js="const path=require('path'),os=require('os');let s;try{s=require(require.resolve('sharp',{paths:[process.argv[3]]}))}catch(e){const root=process.env.POST_BUILDER_NODE_MODULES||path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');s=require(path.join(root,'sharp'))}s(process.argv[1]).png().toFile(process.argv[2]);"
        subprocess.run(['node','-e',js,str(self.project/'preview/export.svg'),str(full),str(REAL_ROOT)],check=True)
        joined=Image.new('RGB',(1080,manifest['height']));y=0
        for row in manifest['images']:
            with Image.open(out/row['file']) as im:joined.paste(im.convert('RGB'),(0,y));y+=im.height
        with Image.open(full) as im:self.assertIsNone(ImageChops.difference(joined,im.convert('RGB')).getbbox())

if __name__=='__main__':unittest.main()
