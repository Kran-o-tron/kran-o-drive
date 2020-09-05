from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)
for i in range(1, 1000):
    txt = str(i)
    pdf.cell(0, 100, txt=txt, ln=i)

pdf.output('test.pdf')
