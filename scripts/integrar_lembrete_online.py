from pathlib import Path

p = Path("site/index.html")
s = p.read_text(encoding="utf-8")

if "GleisonAndroid.agendarLembrete" in s:
    print("Lembrete nativo já está integrado no sistema online.")
else:
    old = "localStorage.setItem('gleison_telefone', telefoneNumeros);\n    closeBooking();"
    new = """localStorage.setItem('gleison_telefone', telefoneNumeros);
    if(window.GleisonAndroid && typeof window.GleisonAndroid.agendarLembrete==='function'){
      window.GleisonAndroid.agendarLembrete(
        dataHora,
        'Gleison Barbearia',
        'Seu horário é em aproximadamente 3 minutos, às '+selectedTime+' — '+servico+'.'
      );
    }
    closeBooking();"""
    if old in s:
        s = s.replace(old, new, 1)
    else:
        marker = "closeBooking();"
        if marker not in s:
            raise SystemExit("Não encontrei o ponto de confirmação do agendamento.")
        s = s.replace(
            marker,
            """if(window.GleisonAndroid && typeof window.GleisonAndroid.agendarLembrete==='function'){
      window.GleisonAndroid.agendarLembrete(dataHora, 'Gleison Barbearia', 'Seu horário é em aproximadamente 3 minutos.');
    }
    """ + marker,
            1
        )

p.write_text(s, encoding="utf-8")

checks = [
    "GleisonAndroid.agendarLembrete",
    "aproximadamente 3 minutos"
]
for item in checks:
    if item not in s:
        raise SystemExit("Validação falhou: " + item)

print("Integração do lembrete nativo no sistema online concluída.")
