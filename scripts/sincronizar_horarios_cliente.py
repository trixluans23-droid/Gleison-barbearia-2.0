from pathlib import Path
import re

p=Path("site/index.html")
s=p.read_text(encoding="utf-8")

old=re.search(r"function horarioFuncionamentoCliente\(\)\{.*?\n\}\n\nfunction estaDentroDoHorarioCliente\(\)",s,re.S)
if not old:
    raise SystemExit("horarioFuncionamentoCliente não encontrado")

new="""let horariosFuncionamentoCliente={abertura:'09:00',fechamento:'20:30',fechamentoSabado:'23:00'};
let excecoesFuncionamentoCliente={};

async function carregarHorariosFuncionamentoCliente(){
  try{
    const {data,error}=await supabaseClient.rpc('obter_horarios_funcionamento',{});
    if(error) throw error;
    const row=Array.isArray(data)?data[0]:data;
    if(row){
      horariosFuncionamentoCliente={
        abertura:String(row.hora_abertura||'09:00').slice(0,5),
        fechamento:String(row.hora_fechamento||'20:30').slice(0,5),
        fechamentoSabado:String(row.hora_fechamento_sabado||'23:00').slice(0,5)
      };
    }
  }catch(error){console.error('Erro ao carregar horários:',error);}
}

async function carregarExcecaoFuncionamentoCliente(date){
  if(!date) return null;
  try{
    const {data,error}=await supabaseClient.rpc('listar_excecoes_funcionamento',{p_inicio:date,p_fim:date});
    if(error) throw error;
    const row=Array.isArray(data)?(data[0]||null):data;
    excecoesFuncionamentoCliente[date]=row||null;
    return row||null;
  }catch(error){
    console.warn('Erro ao carregar exceção:',error);
    excecoesFuncionamentoCliente[date]=null;
    return null;
  }
}

function minutosHorarioCliente(v){
  const p=String(v||'').slice(0,5).split(':').map(Number);
  return p.length===2 && p.every(Number.isFinite) ? p[0]*60+p[1] : null;
}

function horarioFuncionamentoCliente(data){
  const alvo=data||dataLocalHoje();
  const parts=String(alvo).split('-').map(Number);
  const dia=parts.length===3 && parts.every(Number.isFinite)
    ? new Date(parts[0],parts[1]-1,parts[2]).getDay()
    : new Date().getDay();
  const ex=excecoesFuncionamentoCliente[alvo];
  if(ex && ex.aberta===false) return null;
  if((dia===0 || dia===1) && !(ex && ex.aberta===true)) return null;
  const inicio=minutosHorarioCliente(horariosFuncionamentoCliente.abertura);
  const fim=minutosHorarioCliente(dia===6 ? horariosFuncionamentoCliente.fechamentoSabado : horariosFuncionamentoCliente.fechamento);
  if(inicio===null || fim===null || fim<=inicio) return null;
  return {inicio,fim,fimTexto:(dia===6?horariosFuncionamentoCliente.fechamentoSabado:horariosFuncionamentoCliente.fechamento)};
}

function estaDentroDoHorarioCliente(){
  const h=horarioFuncionamentoCliente(dataLocalHoje());
  if(!h) return false;
  const agora=new Date();
  const minutos=agora.getHours()*60+agora.getMinutes();
  return minutos>=h.inicio && minutos<h.fim;
}"""
s=s[:old.start()]+new+s[old.end():]

old2=re.search(r"const timesWeekday = .*?function nomeDiaFechado\(date\)\{.*?\n\}",s,re.S)
if not old2:
    raise SystemExit("bloco de horários do agendamento não encontrado")

new2="""function gerarHorariosFuncionamentoCliente(inicio,fim){
  const lista=[];
  for(let m=inicio;m<=fim;m+=30){
    if(m>11*60 && m<14*60) continue;
    lista.push(String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0'));
  }
  return lista;
}

function getTimesForDate(date){
  const h=horarioFuncionamentoCliente(date);
  return h ? gerarHorariosFuncionamentoCliente(h.inicio,h.fim) : [];
}

function dataFechadaPorDia(date){
  if(!date) return false;
  const parts=date.split('-').map(Number);
  if(parts.length!==3 || parts.some(Number.isNaN)) return false;
  const weekday=new Date(parts[0],parts[1]-1,parts[2]).getDay();
  const ex=excecoesFuncionamentoCliente[date];
  if(ex && ex.aberta===true) return false;
  if(ex && ex.aberta===false) return true;
  return weekday===0 || weekday===1;
}
function nomeDiaFechado(date){
  if(!date) return 'data';
  const parts=date.split('-').map(Number);
  const weekday=new Date(parts[0],parts[1]-1,parts[2]).getDay();
  return ['domingo','segunda-feira','terça-feira','quarta-feira','quinta-feira','sexta-feira','sábado'][weekday] || 'data';
}"""
s=s[:old2.start()]+new2+s[old2.end():]

# Carrega a configuração antes de renderizar a agenda.
open_marker="async function openBooking(){"
if open_marker in s and "await carregarHorariosFuncionamentoCliente();" not in s[s.index(open_marker):s.index(open_marker)+500]:
    s=s.replace(open_marker,open_marker+"\n  await carregarHorariosFuncionamentoCliente();\n  const dataInicial=document.getElementById('date')?.value;\n  if(dataInicial) await carregarExcecaoFuncionamentoCliente(dataInicial);",1)

# Recarrega a configuração sempre que o cliente troca a data.
needle="if(dateInput) dateInput.addEventListener('change', async function(){\n  selectedTime="";"
if needle in s:
    s=s.replace(needle,"if(dateInput) dateInput.addEventListener('change', async function(){\n  selectedTime="";\n  await carregarHorariosFuncionamentoCliente();\n  await carregarExcecaoFuncionamentoCliente(dateInput.value);",1)

p.write_text(s,encoding="utf-8")
print("OK")
