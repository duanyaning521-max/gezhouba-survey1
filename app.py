from flask import Flask, request, render_template_string, Response
import sqlite3, csv, io, os
from datetime import datetime
app=Flask(__name__); DB='survey.db'; ADMIN_KEY=os.environ.get('ADMIN_KEY','123456')
QUESTIONS=['环境卫生满意度','卫生间卫生满意度','餐饮价格及服务满意度','工作人员服务态度满意度','葛洲坝高速服务站整体满意度']
OPTIONS=['非常满意','满意','一般','不满意','非常不满意']
SURVEY='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>葛洲坝高速服务站满意度调查</title><style>body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC";background:#f5f6f8;padding:20px}.card{max-width:650px;margin:auto;background:#fff;border-radius:14px;padding:22px}h1{text-align:center}.q{margin:24px 0}.o{display:block;padding:11px;border:1px solid #ddd;border-radius:8px;margin:8px 0}textarea{width:100%;box-sizing:border-box}button{width:100%;padding:13px;border:0;border-radius:9px;background:#1677ff;color:#fff;font-size:17px}</style><div class="card"><h1>葛洲坝高速服务站满意度调查</h1><p>感谢您的参与，请根据本次服务体验填写。</p><form method="post">{% for i,q in enumerate(questions,1) %}<div class="q"><b>{{i}}. {{q}}</b>{% for o in options %}<label class="o"><input type="radio" name="q{{i}}" value="{{o}}" required> {{o}}</label>{% endfor %}</div>{% endfor %}<div class="q"><b>意见建议（选填）</b><textarea name="suggestion" rows="5"></textarea></div><button>提交问卷</button></form></div>'''
THANKS='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>提交成功</title><style>body{font-family:-apple-system;padding:80px 20px;text-align:center}h1{color:#1677ff}</style><h1>提交成功，感谢您的参与！</h1><p>您的意见已经记录。</p>'''
ADMIN='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>问卷后台</title><style>body{font-family:-apple-system;padding:20px}table{border-collapse:collapse;width:100%;font-size:12px}th,td{border:1px solid #ddd;padding:6px}a{display:inline-block;margin-bottom:15px}</style><h2>葛洲坝高速服务站问卷数据</h2><a href="/admin/export?key={{key}}">导出 CSV</a><table><tr><th>时间</th>{% for q in questions %}<th>{{q}}</th>{% endfor %}<th>意见建议</th></tr>{% for r in rows %}<tr><td>{{r[1]}}</td>{% for x in r[2:7] %}<td>{{x}}</td>{% endfor %}<td>{{r[7]}}</td></tr>{% endfor %}</table>'''
def init():
 c=sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS responses(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,q1 TEXT,q2 TEXT,q3 TEXT,q4 TEXT,q5 TEXT,suggestion TEXT)'); c.commit(); c.close()
@app.route('/',methods=['GET','POST'])
def survey():
 if request.method=='POST':
  v=[request.form.get(f'q{i}') for i in range(1,6)]; s=request.form.get('suggestion',''); c=sqlite3.connect(DB); c.execute('INSERT INTO responses(created_at,q1,q2,q3,q4,q5,suggestion) VALUES(?,?,?,?,?,?,?)',[datetime.now().strftime('%Y-%m-%d %H:%M:%S'),*v,s]); c.commit(); c.close(); return THANKS
 return render_template_string(SURVEY,questions=QUESTIONS,options=OPTIONS,enumerate=enumerate)
@app.route('/admin')
def admin():
 if request.args.get('key')!=ADMIN_KEY:return '无权限',403
 c=sqlite3.connect(DB); rows=c.execute('SELECT * FROM responses ORDER BY id DESC').fetchall(); c.close(); return render_template_string(ADMIN,rows=rows,questions=QUESTIONS,key=ADMIN_KEY)
@app.route('/admin/export')
def export():
 if request.args.get('key')!=ADMIN_KEY:return '无权限',403
 c=sqlite3.connect(DB); rows=c.execute('SELECT * FROM responses ORDER BY id DESC').fetchall(); c.close(); out=io.StringIO(); w=csv.writer(out); w.writerow(['编号','提交时间',*QUESTIONS,'意见建议']); w.writerows(rows); return Response('\ufeff'+out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=gezhouba_survey.csv'})
init()
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
