#define X_STEP_PIN 54       // PIN de pulsos para avanzar el motor
#define X_DIR_PIN 55        // PIN para indicar la di_Xreccion en la que debe avanzar
#define X_ENABLE_PIN 38
#define X_MIN_PIN 3         // PIN para el fin de carrera colocado al inicio del recorrido
#define X_MAX_PIN 2         // PIN para el fin de carrera colocado al final del recorrido

bool fc_inic_X, fc_fin_X = true; //variables de lectura de los fin de carrera
bool direccion = false; 
int i, j, w = 0 ; // diversos contadores
int v = 30;

void setup() {
  // put your setup code here, to run once:
  pinMode(X_STEP_PIN, OUTPUT);      // Pasos del motor X
  pinMode(X_DIR_PIN, OUTPUT);       // di_X  direccion del motor X
  pinMode(X_ENABLE_PIN, OUTPUT);
  pinMode(X_MIN_PIN, INPUT_PULLUP);        // Fin de carrera inicio X
  pinMode(X_MAX_PIN, INPUT_PULLUP);        // Fin de carrera terminal X

  digitalWrite(X_ENABLE_PIN, LOW);
}

void loop() 
{
switch (v)
  {
    case 1: // velocidad = 1 mm/h
      for (int i = 0; i < 2544; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 2:
      for (int i = 0; i < 1272; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 3:
      for (int i = 0; i < 848; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 4:
      for (int i = 0; i < 636; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 5:
      for (int i = 0; i < 508; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 6:
      for (int i = 0; i < 424; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 7:
      for (int i = 0; i < 362; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 8:
      for (int i = 0; i < 318; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 9:
      for (int i = 0; i < 282; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 10:
      for (int i = 0; i < 254; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 20:
      for (int i = 0; i < 126; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 30:
      for (int i = 0; i < 84; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 40:
      for (int i = 0; i < 62; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 50:
      for (int i = 0; i < 50; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 60:
      for (int i = 0; i < 42; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 70:
      for (int i = 0; i < 36; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          if (i < 32)
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(208);
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(208);
          }
          else
          {
            digitalWrite(X_STEP_PIN,LOW);
            delayMicroseconds(208);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      break;
    case 80:
      for (int i = 0; i < 32; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          digitalWrite(X_STEP_PIN, HIGH);
          delayMicroseconds(207);
          digitalWrite(X_STEP_PIN, LOW);
          delayMicroseconds(207);
        }
        else
        {
          digitalWrite(X_STEP_PIN,LOW);
          delayMicroseconds(207);
        }
      }
      break;
    case 90:
      for (int i = 0; i < 32; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          digitalWrite(X_STEP_PIN, HIGH);
          delayMicroseconds(184);
          digitalWrite(X_STEP_PIN, LOW);
          delayMicroseconds(184);
        }
        else
        {
          digitalWrite(X_STEP_PIN,LOW);
          delayMicroseconds(184);
        }
      }
      break;
    default:
      for (int i = 0; i < 32; i++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false and fc_inic_X == false)
        {
          digitalWrite(X_STEP_PIN, HIGH);
          delayMicroseconds(165);
          digitalWrite(X_STEP_PIN, LOW);
          delayMicroseconds(165);
        }
        else
        {
          digitalWrite(X_STEP_PIN,LOW);
          delayMicroseconds(165);
        }
      }
      break;
  }
}
