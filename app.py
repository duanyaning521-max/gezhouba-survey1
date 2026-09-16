from flask import Flask, request, redirect, render_template, Response
import sqlite3, csv, io, os
from datetime import datetime, date, timedelta

app = Flask(__name__)
DB = "survey.db"
ADMIN_KEY = os.environ.get("ADMIN_KEY", "123456")
QUESTIONS = ["环境卫生满意度","卫生间卫生满意度","餐饮价格及服务满意度","工作人员服务态度满意度","葛洲坝高速服务站整体满意度"]
OPTIONS = ["非常满意","满意","一般","不满意","非常不满意"]

def db():
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    return con

def init_db():
    con=db()
    con.execute("""CREATE TABLE IF NOT EXISTS responses(
      id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT,
      q1 TEXT,q2 TEXT,q3 TEXT,q4 TEXT,q5 TEXT,suggestion TEXT)""")
    con.commit(); con.close()
init_db()

@app.route("/", methods=["GET","POST"])
def survey():
    if request.method=="POST":
        vals=[request.form.get(f"q{i}") for i in range(1,6)]
        con=db()
        con.execute("INSERT INTO responses(created_at,q1,q2,q3,q4,q5,suggestion) VALUES(?,?,?,?,?,?,?)",
          [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),*vals,request.form.get("suggestion","")])
        con.commit(); con.close()
        return render_template("thanks.html")
    return render_template("survey.html", questions=QUESTIONS, options=OPTIONS)

def auth():
    return request.args.get("key")==ADMIN_KEY

def stats(rows):
    total=len(rows)
    counts=[]
    for i in range(1,6):
        c={o:0 for o in OPTIONS}
        for r in rows: c[r[f"q{i}"]]=c.get(r[f"q{i}"],0)+1
        counts.append(c)
    satisfied=sum(sum(counts[i][o] for o in ["非常满意","满意"]) for i in range(5))
    rate=round(satisfied/(total*5)*100,1) if total else 0
    return total, counts, rate

@app.route("/admin")
def admin():
    if not auth(): return "无权限，请使用正确的管理密码。",403
    period=request.args.get("period","all")
    con=db()
    if period=="today":
        rows=con.execute("SELECT * FROM responses WHERE date(created_at)=date('now','localtime') ORDER BY id DESC").fetchall()
    elif period=="7":
        rows=con.execute("SELECT * FROM responses WHERE datetime(created_at)>=datetime('now','-7 days','localtime') ORDER BY id DESC").fetchall()
    elif period=="30":
        rows=con.execute("SELECT * FROM responses WHERE datetime(created_at)>=datetime('now','-30 days','localtime') ORDER BY id DESC").fetchall()
    else:
        rows=con.execute("SELECT * FROM responses ORDER BY id DESC").fetchall()
    con.close()
    total,counts,rate=stats(rows)
    return render_template("admin.html",rows=rows,questions=QUESTIONS,options=OPTIONS,
                           counts=counts,total=total,rate=rate,period=period,key=ADMIN_KEY)

@app.route("/admin/export")
def export():
    if not auth(): return "无权限",403
    con=db(); rows=con.execute("SELECT * FROM responses ORDER BY id DESC").fetchall(); con.close()
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(["编号","提交时间",*QUESTIONS,"意见建议"])
    for r in rows: w.writerow([r["id"],r["created_at"],r["q1"],r["q2"],r["q3"],r["q4"],r["q5"],r["suggestion"]])
    return Response("\ufeff"+out.getvalue(),mimetype="text/csv",
      headers={"Content-Disposition":"attachment; filename=gezhouba_survey.csv"})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
