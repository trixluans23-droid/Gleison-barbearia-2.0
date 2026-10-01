from pathlib import Path
import re

p=Path("site/index.html")
s=p.read_text(encoding="utf-8")

# Garante que a agenda de terça a sexta tenha horários até 23:00.
padrao=r'(const\s+timesWeekday\s*=\s*\[[^\]]*?)"20:30"'
s,n=re.subn(padrao,r'\1"20:30","21:00","21:30","22:00","22:30","23:00"',s,count=1)
if n==0:
    # Versão alternativa caso a lista use outra formatação.
    s=s.replace('const timesWeekday = ["09:00","09:30","10:00","10:30","11:00","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30","20:00","20:30"];',
                'const timesWeekday = ["09:00","09:30","10:00","10:30","11:00","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30","20:00","20:30","21:00","21:30","22:00","22:30","23:00"];')

# Domingo e segunda continuam fechados; terça-feira não deve mais ser bloqueada.
s=s.replace('return weekday===0 || weekday===1 || weekday===2;', 'return weekday===0 || weekday===1;')
s=s.replace('if(weekday===0 || weekday===1 || weekday===2) return [];', 'if(weekday===0 || weekday===1) return [];')

# Se existir o horário comercial fixo antigo, atualiza também o aviso visual para 23:00.
s=s.replace("return {inicio:9*60, fim:20*60+30, fimTexto:'20:30'};",
            "return {inicio:9*60, fim:23*60, fimTexto:'23:00'};")

p.write_text(s,encoding="utf-8")
print("Horários até 23:00 aplicados à agenda do cliente.")
