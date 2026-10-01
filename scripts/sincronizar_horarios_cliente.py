from pathlib import Path
import re

p = Path("site/index.html")
s = p.read_text(encoding="utf-8")

# Acrescenta slots de 30 minutos até 23:00 à lista legada.
padrao = r'(const\s+timesWeekday\s*=\s*\[[^\]]*?)"20:30"'
s, n = re.subn(padrao, r'\1"20:30","21:00","21:30","22:00","22:30","23:00"', s, count=1)
if n == 0:
    s = s.replace(
        'const timesWeekday = ["09:00","09:30","10:00","10:30","11:00","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30","20:00","20:30"];',
        'const timesWeekday = ["09:00","09:30","10:00","10:30","11:00","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30","20:00","20:30","21:00","21:30","22:00","22:30","23:00"];'
    )

# Domingo e segunda fechados; terça-feira liberada.
s = s.replace('return weekday===0 || weekday===1 || weekday===2;', 'return weekday===0 || weekday===1;')
s = s.replace('if(weekday===0 || weekday===1 || weekday===2) return [];', 'if(weekday===0 || weekday===1) return [];')

# Mantém o aviso legado coerente.
s = s.replace(
    "return {inicio:9*60, fim:20*60+30, fimTexto:'20:30'};",
    "return {inicio:9*60, fim:23*60, fimTexto:'23:00'};"
)

# A agenda atual gera os slots dentro de renderTimes(). Usa os horários salvos no Supabase.
old_limite = "const limiteSabado = new Date(data+'T12:00:00').getDay()===6 ? 23*60 : 20*60+30;"
new_limite = '''let inicioAgenda=9*60;
    let limiteSabado=23*60;
    try{
      const {data:horarioFuncionamento,error:horarioError}=await supabaseClient.rpc('obter_horarios_funcionamento',{});
      if(horarioError) throw horarioError;
      const row=Array.isArray(horarioFuncionamento)?horarioFuncionamento[0]:horarioFuncionamento;
      const parseMin=v=>{
        const p=String(v||'').slice(0,5).split(':').map(Number);
        return p.length===2 && p.every(Number.isFinite) ? p[0]*60+p[1] : null;
      };
      const abertura=parseMin(row && row.hora_abertura);
      const fechamento=parseMin(new Date(data+'T12:00:00').getDay()===6
        ? (row && row.hora_fechamento_sabado)
        : (row && row.hora_fechamento));
      if(abertura!==null) inicioAgenda=abertura;
      if(fechamento!==null) limiteSabado=fechamento;
    }catch(e){
      console.warn('Não foi possível carregar o horário de funcionamento:',e);
    }'''
if old_limite not in s:
    raise SystemExit("limite fixo não encontrado no HTML")
s = s.replace(old_limite, new_limite, 1)

# Usa a abertura configurada também na variável de início da agenda.
s = s.replace('const inicio=9*60;', 'const inicio=inicioAgenda;')

# Corrige aspas escapadas no HTML do histórico do cliente para manter o JavaScript válido.
s = s.replace("\\\\'", "\\'")
# Garante que o bloco real de renderTimes() nunca volte a ignorar a abertura configurada.
s = s.replace('const inicio=9*60;\\n    const horarios=[];', 'const inicio=inicioAgenda;\\n    const horarios=[];')

# Usa a abertura configurada nos loops que ainda começavam às 09:00.
s = s.replace('for(let m=9*60;', 'for(let m=inicioAgenda;')
s = s.replace('for(let i=9*60;', 'for(let i=inicioAgenda;')
s = s.replace('for(let t=9*60;', 'for(let t=inicioAgenda;')

# Atualização rápida enquanto a tela de agendamento está aberta.
s = s.replace('},15000);', '},2000);')

p.write_text(s, encoding="utf-8")
print("Horários configuráveis aplicados à agenda do cliente.")
