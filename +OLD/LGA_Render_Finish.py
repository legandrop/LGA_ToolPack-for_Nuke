import nuke
import os
import datetime
from PySide2.QtMultimedia import QSound
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def Set_Render_Start_Time():
    if not nuke.root().knob("Km_Render_Start_Time"):
        nuke.root().addKnob(nuke.EvalString_Knob("Km_Render_Start_Time"))
        nuke.root().knob("Km_Render_Start_Time").setVisible(False)

    Current_time_str = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    nuke.root().knob("Km_Render_Start_Time").setValue(Current_time_str)

def Get_Time_Duration():
    time1_str = nuke.root().knob("Km_Render_Start_Time").getValue()
    time1 = datetime.datetime.strptime(time1_str, '%Y-%m-%d %H:%M:%S')
    time2 = datetime.datetime.now()
    duration = time2 - time1
    duration_in_s = duration.total_seconds()
    hours, remainder = divmod(duration_in_s, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def send_email(subject, body, to_email):
    from_email = os.getenv('Nuke_Write_Mail_From', 'default_from_email@example.com')
    password = os.getenv('Nuke_Write_Mail_Pass', 'default_password')

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.close()
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

def Render_Finished():
    render_time = Get_Time_Duration()
    print(f"Render Time: {render_time}")

    # Reproducir el sonido
    sound_file_path = os.path.join(os.path.dirname(__file__), 'LGA_Render_Finish.wav')
    QSound.play(sound_file_path)

    # Verificar si el knob "send_mail" existe y esta activado
    write_node = nuke.thisNode()
    send_mail_state = False
    if 'send_mail' in write_node.knobs():
        send_mail_state = write_node['send_mail'].value()

    if send_mail_state:
        # Obtener el destinatario del correo electronico de las variables de entorno
        to_email = os.getenv('Nuke_Write_Mail_To', 'default_to_email@example.com')

        # Formatear el cuerpo del correo
        script_name = os.path.basename(nuke.root().name())
        render_directory = os.path.dirname(write_node.knob('file').value())
        render_file = write_node.knob('file').getEvaluatedValue()
        body = (f"Script Name: {script_name}\n"
                f"Render Directory: {render_directory}\n"
                f"Render File: {render_file}\n"
                f"Render Time: {render_time}\n"
                "El render ha finalizado exitosamente.")

        # Enviar correo electronico
        send_email(
            subject="Render Finished",
            body=body,
            to_email=to_email
        )

# Agregar callbacks de Nuke
nuke.addBeforeRender(Set_Render_Start_Time)
nuke.addAfterRender(Render_Finished)
