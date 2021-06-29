from kadi.events import rad_zones
from cxotime import CxoTime
import acispy
import matplotlib.pyplot as plt
from pathlib import Path
import smtplib
from email.message import EmailMessage

outdir = Path('/proj/web-cxc/htdocs/acis/cr_fp_plots')

tstart = CxoTime("2021:100:00:00:00")
tstop = CxoTime()

rzs = rad_zones.filter(start=tstart, stop=tstop)

ds = acispy.EngArchiveData(tstart, tstop, ["1crat", "1crbt", "fptemp_11", "earth_solid_angle"])

last_time = max(ds["fptemp_11"].times[-1].value, 
                ds["1crat"].times[-1].value, 
                ds["1crbt"].times[-1].value)

plt.rc("axes", linewidth=2)
fns = []
news = []
for rz in rzs:
    if last_time < rz.tstart or rz.tstart < last_time < rz.tstop:
        continue
    fn = f"{rz.start[:11].replace(':', '_')}_{rz.start[:11].replace(':', '_')}.png"
    fn = outdir / fn
    fns.append(fn)
    if fn.exists():
        news.append(False)
    else:
        fptemp = ds["fptemp_11"][rz.start:rz.stop]
        crat = ds["1crat"][rz.start:rz.stop]
        crbt = ds["1crbt"][rz.start:rz.stop]
        esa = ds["earth_solid_angle"][rz.start:rz.stop]
        dp = acispy.CustomDatePlot(fptemp.times, fptemp, lw=2)
        acispy.CustomDatePlot(crat.times, crat, plot=dp, lw=2)
        acispy.CustomDatePlot(crbt.times, crbt, plot=dp, lw=2)
        dp.plot_right(esa.times, esa)
        dp.add_hline(-90, color='gold', lw=4)
        dp.add_hline(-80, color='red', lw=4)
        dp.add_hline(-84, color='green', ls='--', lw=2)
        dp.add_hline(-80, color='gold', ls='--', lw=2)
        dp.add_vline(rz.perigee, lw=2, color='dodgerblue', ls='--')
        dp.add_vline(rz.start, lw=2, color='dodgerblue', ls='--')
        dp.add_vline(rz.stop, lw=2, color='dodgerblue', ls='--')
        ymin = min(fptemp.value.min(), crat.value.min(), crbt.value.min())-2
        ymax = max(fptemp.value.max(), crat.value.max(), crbt.value.max())+2
        dp.set_ylim(ymin, ymax)
        dp.set_ylabel("Temperature ($^\circ$C)")
        dp.ax2.set_ylabel("Earth Solid Angle (sr)", fontsize=18)
        dp.ax.tick_params(which="major", width=2, length=6)
        dp.ax.tick_params(which="minor", width=2, length=3)
        dp.ax2.tick_params(which="major", width=2, length=6)
        title = f"{rz.start} - {rz.stop}\n"
        title += f"FPTEMP_11 Max: {fptemp.value.max():.2f} $^\circ$C\n"
        title += f"1CRAT Max: {crat.value.max():.2f} $^\circ$C\n"
        title += f"1CRBT Max: {crbt.value.max():.2f} $^\circ$C"
        dp.set_title(title)
        dp.savefig(fn, bbox_inches='tight')
        news.append(True)

outlines = [
    "<html>\n",
    "<body>\n",
    "<h1>ACIS FP Temperature, 1CRAT, and 1CRBT at Every Perigee</h1>\n",
    "<ul>\n",
]
for new, fn in zip(news, fns):
    f = fn.name
    words = f.split(".")[0].split("_")
    newstr = "<font color=\"red\">NEW!</font>" if new else ""
    outlines += [
        f"<li><a href=\"{f}\">{':'.join(words[0:3])}</a> {newstr}</li>\n",
        "<p />\n"
    ]
outlines += [
    "</ul>\n",
    "</body>\n",
    "</html>"
]

with open(outdir / "index.html", "w") as f:
    f.writelines(outlines)

if any(news):

    email_txt = "A new plot showing the ACIS FP and Cold Radiator Temperatures from "
    email_txt += "the last perigee has appeared at https://cxc.cfa.harvard.edu/acis/cr_fp_plots."

    msg = EmailMessage()
    msg['Subject'] = "ACIS FP and Cold Radiator Temperatures from the last Perigee"
    msg['From'] = "john.zuhone@cfa.harvard.edu"
    msg['To'] = "john.zuhone@cfa.harvard.edu"
    msg.set_content(email_txt)

    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)

