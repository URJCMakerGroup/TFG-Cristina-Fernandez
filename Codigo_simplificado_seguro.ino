// Biblioteca de la pantalla LCD
#include <EEPROM.h>
#include <LiquidCrystal.h>
LiquidCrystal lcd(16, 17, 23, 25, 27, 29);

//Pines de la shield
#define LCD_PINS_RS 16      // LCD control conectado a GADGETS3D  shield LCDRS
#define LCD_PINS_ENABLE 17  // LCD enable pin conectado a GADGETS3D shield LCDE
#define LCD_PINS_D4 23      // LCD signal pin, conectado a GADGETS3D shield LCD4
#define LCD_PINS_D5 25      // LCD signal pin, conectado a GADGETS3D shield LCD5
#define LCD_PINS_D6 27      // LCD signal pin, conectado a GADGETS3D shield LCD6
#define LCD_PINS_D7 29      // LCD signal pin, conectado a GADGETS3D shield LCD7
#define BTN_EN1 31          // Encoder, conectado a GADGETS3D shield S_E1
#define BTN_EN2 33          // Encoder, cconectado a GADGETS3D shield S_E2
#define BTN_ENC 35          // Encoder Click, connected to Gadgets3D shield S_EC
#define X_STEP_PIN 54       // PIN de pulsos para avanzar el motor
#define X_DIR_PIN 55        // PIN para indicar la di_Xreccion en la que debe avanzar
#define X_ENABLE_PIN 38     // PIN de lectura/escritura
#define X_MIN_PIN 3         // PIN para el fin de carrera colocado al inicio del recorrido (1: presionado (true))
#define X_MAX_PIN 2         // PIN para el fin de carrera colocado al final del recorrido

//Signos necesarios
byte empty[8] =
{
  B00000,
  B00100,
  B01010,
  B10001,
  B10001,
  B01010,
  B00100,
};
byte full[8] =
{
  B00000,
  B00100,
  B01110,
  B11111,
  B11111,
  B01110,
  B00100,
};
byte micro[8] =
{
  B00000,
  B10001,
  B10001,
  B11011,
  B10101,
  B10000,
  B10000,
};
byte arrow[8] =
{
  B00000,
  B00001,
  B00001,
  B00001,
  B01001,
  B11111,
  B01000,
};

//variables internas
bool btn_en1, btn_en2, btn_enc, btn_en1_prev, btn_en2_prev ;       //variables de lectura directa del encoder
bool fc_inic_X, fc_fin_X = true;                                   //variables de lectura de los fin de carrera
bool direccion = false;                                            //false es hacia 0 y true hacia 400
bool derecha, izquierda, pulsador = false;                         // variables de lectura del encoder interpretadas
int volatile estado, estado_ant = 0;                               // Variables del estado (valores de 0 a 5)
int fila, columna = 0;                                             // Variable de fila en la pantalla lcd
int i = 0;                                                         // contador de pulsos
int j = 0;                                                         // contador
int w = 0;                                                         // contador de micropasos medios
int w_final = 0;                                                   // numero de medios micropasos en función de la velocidad
int t_espera = 0;                                                  // tiempo de espera en función de la velocidad
int di_X, df_X = 0;                                                // variables del ensayo (distancia inicial, distancia final)en mm
int x_eeprom = 0;                                                  // variable de la posicion guardada en la eeprom
int x = 0;                                                       // posicion actual del puente movil
long x_nm = 0L;                                                     // posicion actual del puente movil en nanometros
int v, avance = 1;                                                 // variable para definir la velocidad
int L = 260;                                                       // l es la longitud del husillo, por lo que se trata de la distancia máxima que se puede llevar a cabo
int DIR_EEP = 1;                                                   // direccion de la memoria eeprom

void setup()
{
  pinMode(BTN_EN1, INPUT_PULLUP);     // Encoder 1 ¿es input o input_pullup?
  pinMode(BTN_EN2, INPUT_PULLUP);     // Encoder 2 ¿es input o input_pullup?
  pinMode(BTN_ENC, INPUT_PULLUP);     // Encoder Swith ¿es input o input_pullup?
  pinMode(X_STEP_PIN, OUTPUT);        // Pasos del motor X
  pinMode(X_DIR_PIN, OUTPUT);         // di_X direccion del motor X
  pinMode(X_ENABLE_PIN, OUTPUT);
  pinMode(X_MIN_PIN, INPUT_PULLUP);   // Fin de carrera inicio X
  pinMode(X_MAX_PIN, INPUT_PULLUP);   // Fin de carrera terminal X

  btn_en1 , btn_en1_prev = digitalRead(BTN_EN1);
  btn_en2 , btn_en2_prev = digitalRead(BTN_EN2);
  btn_enc = digitalRead(BTN_ENC);

  lcd.begin(20, 4);   // 20 columnas y 4 filas
  lcd.createChar(0, empty);   // 0: numero de carácter; empty: matriz que contiene los pixeles del carácter
  lcd.createChar(1, full);    // 1: numero de carácter; full: matriz que contiene los pixeles del carácter
  lcd.createChar(2, micro);   // 2: numero de carácter; micro: matriz que contiene los pixeles del carácter
  lcd.createChar(3, arrow);   // 3: número de carácter; arrow: matriz que contiene los pixeles del carácter
}

void leer_encoder()
{
  btn_en1 = digitalRead(BTN_EN1);
  btn_en2 = digitalRead(BTN_EN2);
  fc_inic_X = digitalRead(X_MIN_PIN);
  fc_fin_X  = digitalRead(X_MAX_PIN);
  digitalWrite(X_DIR_PIN, direccion);

  if (btn_en1 != btn_en1_prev || btn_en2 != btn_en2_prev)
  {
    if (btn_en2 == false & btn_en1 == false & btn_en2_prev == true & btn_en1_prev == false)
    {
      derecha = true;
      izquierda = false;
    }
    else if ( btn_en2 == false & btn_en1 == false & btn_en2_prev == false & btn_en1_prev == true )
    {
      derecha = false;
      izquierda = true;
    }
    else
    {
      derecha = false;
      izquierda = false;
    }
  }
  else
  {
    derecha = false;
    izquierda = false;
  }
  btn_en1_prev = btn_en1;
  btn_en2_prev = btn_en2;
}

void leer_pulso()
{
  btn_enc = digitalRead(BTN_ENC);

  if (btn_enc == false) //Detector de flanco del pulsador
  {
    i++;
  }
  if (i >= 80)
  {
    pulsador = true;
    i = 0;
    delay(200);
  }
  else
  {
    pulsador = false;
  }
}

/////////////////Estado 0: INICIO/////////////////
void comprobar_pos_eep()
{
  EEPROM.get(DIR_EEP, x_eeprom);   //Leer memoria EEPROM direccion 0
  fc_inic_X = digitalRead(X_MIN_PIN);
  fc_fin_X  = digitalRead(X_MAX_PIN);

  if (fc_inic_X == true)  // estamos en x = 0
  {
    // se puede comprobar que fc_fin_X no esta true porque sería un error
    if (x_eeprom != 0)
    {
      x_eeprom = 0;
      EEPROM.put(DIR_EEP, x_eeprom); // como la x_eeprom era incorrecta lo actualizamos con el final de carrera
    }
  }
  else if (fc_fin_X == true)  // estamos en x = l
  {
    if (x_eeprom != L)
    {
      x_eeprom = L;
      EEPROM.put(DIR_EEP, x_eeprom); // como la x_eeprom era incorrecta lo actualizamos con el final de carrera
    }
  }
  else if (x_eeprom == 0 || x_eeprom == L)  // la eeprom me dice que estoy a 0 pero el final de carrera no esta presionado (EPROMM incorrecto)
  {
    x_eeprom = -1;
    EEPROM.put(DIR_EEP, x_eeprom);
  }
}

void pantalla_inicio()
{
  lcd.clear();
  lcd.setCursor(2, 0);    // posiciona el cursor en la columna 1 fila 0
  lcd.print("ENSAYO DE MODELO");
  lcd.setCursor(3, 1);    // posiciona el cursor en la columna 1 fila 1
  lcd.print("ANALOGO SIMPLE");
  lcd.setCursor(2, 2);
  lcd.print("Dist actual:");
  lcd.print(" ");
  if (x_eeprom < 0)
  {
    lcd.print("?");
  }
  else
  {
    lcd.print(x_eeprom);
    lcd.print("mm");
  }
  lcd.setCursor(0, 3);    // posiciona el cursor en la columna 1 fila 3
  lcd.print("Iniciar Experimento");
}

/////////////////Estado 1: MENÚ/////////////////
void menu()
{
  fila, columna = 0;
  di_X = 0;
  df_X = 0;
  v = 1;
  x = x_eeprom;

  lcd.clear();
  lcd.setCursor(1, 0);
  lcd.print("dist.iniX");
  lcd.setCursor(12, 0);
  lcd.print(di_X);
  lcd.setCursor(18, 0);
  lcd.print("mm");
  lcd.setCursor(1, 1);
  lcd.print("dist.finX");
  lcd.setCursor(12, 1);
  lcd.print(df_X);
  lcd.setCursor(18, 1);
  lcd.print("mm");
  lcd.setCursor(1, 2);
  lcd.print("velocidad");
  lcd.setCursor(12, 2);
  lcd.print(v);
  lcd.setCursor(16, 2);
  lcd.print("mm/h");
  lcd.setCursor(1, 3);
  lcd.print("Iniciar experimento");
  lcd.setCursor(0, 0);
  lcd.write(byte(0));
  lcd.setCursor(0, 1);
  lcd.write(byte(0));
  lcd.setCursor(0, 2);
  lcd.write(byte(0));
  lcd.setCursor(0, 3);
  lcd.write(byte(0));
  lcd.setCursor(0, fila);
  lcd.write(byte(1));
}

/////////////////Estado 2: DEFINICIÓN DE VARIABLES/////////////////
void DefinicionDeVariables()
{
  switch (fila)//fila es la variable vertical de la pantalla, indica que variable se esta manipulando
  {
    case 0: //modificar la distancia inicial
      if (pulsador == true  and columna < 3) //columna es una variable que avanza en horizontal por la pantalla, cuando vale 0 podemos cambia en vertical con derecha o izquierda, cuando no aumentamos la variable con la que estemos trabajando
      {
        columna++;
      }
      else if (pulsador == true and columna == 3) //hay 4 opciones
      {
        columna = 0;
      }
      switch (columna)
      {
        case 0: //opción 1: seleccionar variable
          if (derecha == true )
          {
            fila = 1;
            lcd.setCursor(0, 0);
            lcd.write(byte(0));
            lcd.setCursor(0, 1);
            lcd.write(byte(1));
            lcd.setCursor(0, 2);
            lcd.write(byte(0));
            lcd.setCursor(0, 3);
            lcd.write(byte(0));
          }
          else if (izquierda == true)
          {
            fila = 3;
            lcd.setCursor(0, 0);
            lcd.write(byte(0));
            lcd.setCursor(0, 1);
            lcd.write(byte(0));
            lcd.setCursor(0, 2);
            lcd.write(byte(0));
            lcd.setCursor(0, 3);
            lcd.write(byte(1));
          }
          break;
        case 1: //opción 2: ir sumando y restando de 1 en 1
          if (derecha == true and di_X + 1 < L)
          {
            di_X = di_X + 1;
            lcd.setCursor(12, 0);
            lcd.print("   ");
            lcd.setCursor(12, 0);
            lcd.print(di_X);
          }
          else if (izquierda == true and di_X - 1 >= 0)
          {
            di_X = di_X - 1;
            lcd.setCursor(12, 0);
            lcd.print("   ");
            lcd.setCursor(12, 0);
            lcd.print(di_X);
          }
          break;
        case 2: //opción 3: ir sumando y restando de 10 en 10
          if (derecha == true and di_X + 10 < L)
          {
            di_X = di_X + 10;
            lcd.setCursor(12, 0);
            lcd.print("   ");
            lcd.setCursor(12, 0);
            lcd.print(di_X);
          }
          else if (izquierda == true and di_X - 10 >= 0)
          {
            di_X = di_X - 10;
            lcd.setCursor(12, 0);
            lcd.print("   ");
            lcd.setCursor(12, 0);
            lcd.print(di_X);
          }
          break;
        default: //opción 4: ir sumando y restando de 100 en 100
          if (derecha == true and di_X + 100 < L)
          {
            di_X = di_X + 100;
            lcd.setCursor(12, 0);
            lcd.print("   ");
            lcd.setCursor(12, 0);
            lcd.print(di_X);
          }
          else if (izquierda == true and di_X - 100 >= 0)
          {
            di_X = di_X - 100;
            lcd.setCursor(12, 0);
            lcd.print("   ");
            lcd.setCursor(12, 0);
            lcd.print(di_X);
          }
          break;
      }
      break;
    case 1: //modificar la distancia final
      if (pulsador == true  and columna < 3) //columna es una variable que avanza en horizontal por la pantalla, cuando vale 0 podemos cambia en vertical con derecha o izquierda, cuando no aumentamos la variable con la que estemos trabajando
      {
        columna++;
      }
      else if (pulsador == true and columna == 3)
      {
        columna = 0;
      }
      switch (columna)
      {
        case 0: //opción 1: seleccionar variable
          if (derecha == true )
          {
            fila = 2;
            lcd.setCursor(0, 0);
            lcd.write(byte(0));
            lcd.setCursor(0, 1);
            lcd.write(byte(0));
            lcd.setCursor(0, 2);
            lcd.write(byte(1));
            lcd.setCursor(0, 3);
            lcd.write(byte(0));
          }
          else if (izquierda == true)
          {
            fila = 0;
            lcd.setCursor(0, 0);
            lcd.write(byte(1));
            lcd.setCursor(0, 1);
            lcd.write(byte(0));
            lcd.setCursor(0, 2);
            lcd.write(byte(0));
            lcd.setCursor(0, 3);
            lcd.write(byte(0));
          }
          break;
        case 1: //opción 2: ir sumando y restando de 1 en 1
          if (derecha == true and df_X + 1 < L)
          {
            df_X = df_X + 1;
            lcd.setCursor(12, 1);
            lcd.print("   ");
            lcd.setCursor(12, 1);
            lcd.print(df_X);
          }
          else if (izquierda == true and df_X - 1 >= 0)
          {
            df_X = df_X - 1;
            lcd.setCursor(12, 1);
            lcd.print("   ");
            lcd.setCursor(12, 1);
            lcd.print(df_X);
          }
          break;
        case 2: //opción 3: ir sumando y restando de 10 en 10
          if (derecha == true and df_X + 10 < L)
          {
            df_X = df_X + 10;
            lcd.setCursor(12, 1);
            lcd.print("   ");
            lcd.setCursor(12, 1);
            lcd.print(df_X);
          }
          else if (izquierda == true and df_X - 10 >= 0)
          {
            df_X = df_X - 10;
            lcd.setCursor(12, 1);
            lcd.print("   ");
            lcd.setCursor(12, 1);
            lcd.print(df_X);
          }
          break;
        default://opción 4: ir sumando y restando de 100 en 100
          if (derecha == true and df_X + 100 < L)
          {
            df_X = df_X + 100;
            lcd.setCursor(12, 1);
            lcd.print("   ");
            lcd.setCursor(12, 1);
            lcd.print(df_X);
          }
          else if (izquierda == true and df_X - 100 >= 0)
          {
            df_X = df_X - 100;
            lcd.setCursor(12, 1);
            lcd.print("   ");
            lcd.setCursor(12, 1);
            lcd.print(df_X);
          }
          break;
      }
      break;
    case 2: //modificar la velocidad
      if (pulsador == true  and columna < 1) //columna es una variable que avanza en horizontal por la pantalla, cuando vale 0 podemos cambia en vertical con derecha o izquierda, cuando no aumentamos la variable con la que estemos trabajando
      {
        columna++;
      }
      else if (pulsador == true and columna == 1) //hay 2 opciones
      {
        columna = 0;
      }
      switch (columna)
      {
        case 0: //opción 1: seleccionar variable
          if (derecha == true )
          {
            fila = 3;
            lcd.setCursor(0, 0);
            lcd.write(byte(0));
            lcd.setCursor(0, 1);
            lcd.write(byte(0));
            lcd.setCursor(0, 2);
            lcd.write(byte(0));
            lcd.setCursor(0, 3);
            lcd.write(byte(1));
          }
          else if (izquierda == true)
          {
            fila = 1;
            lcd.setCursor(0, 0);
            lcd.write(byte(0));
            lcd.setCursor(0, 1);
            lcd.write(byte(1));
            lcd.setCursor(0, 2);
            lcd.write(byte(0));
            lcd.setCursor(0, 3);
            lcd.write(byte(0));
          }
          break;
        default: //opción 2: modificar la velocidad de 1 en 1 o de 10 en 10 en función de la velocidad
          if (izquierda == true)
          {
            if (v <= 10 and v > 0)
            {
              v = v - 1;
              lcd.setCursor(12, 2);
              lcd.print("   ");
              lcd.setCursor(12, 2);
              lcd.print(v);
            }
            else if (v > 10)
            {
              v = v - 10;
              lcd.setCursor(12, 2);
              lcd.print("   ");
              lcd.setCursor(12, 2);
              lcd.print(v);
            }
          }
          else if (derecha == true)
          {
            if (v < 10)
            {
              v = v + 1;
              lcd.setCursor(12, 2);
              lcd.print("   ");
              lcd.setCursor(12, 2);
              lcd.print(v);
            }
            else if (v >= 10 and v < 100)
            {
              v = v + 10;
              lcd.setCursor(12, 2);
              lcd.print("   ");
              lcd.setCursor(12, 2);
              lcd.print(v);
            }
          }
          break;
      }
      break;
    default: //iniciar experimento
      if (pulsador == true)
      {
        estado = 3;
        //        lcd.clear();
        //        lcd.setCursor(1, 0);
        //        lcd.print("PREPARANDO");
        //        lcd.setCursor(1, 1);
        //        lcd.print("EXPERIMENTO...");
        //        delay(5000);
      }
      else if (derecha == true )
      {
        fila = 0;
        columna = 0;
        lcd.setCursor(0, 0);
        lcd.write(byte(1));
        lcd.setCursor(0, 1);
        lcd.write(byte(0));
        lcd.setCursor(0, 2);
        lcd.write(byte(0));
        lcd.setCursor(0, 3);
        lcd.write(byte(0));
      }
      else if (izquierda == true)
      {
        fila = 2;
        columna = 0;
        lcd.setCursor(0, 0);
        lcd.write(byte(0));
        lcd.setCursor(0, 1);
        lcd.write(byte(0));
        lcd.setCursor(0, 2);
        lcd.write(byte(1));
        lcd.setCursor(0, 3);
        lcd.write(byte(0));
      }
      break;
  }
}

/////////////////Estado 3: MOVER PUENTE MÓVIL/////////////////
void reinicio()
{
  lcd.clear();
  lcd.setCursor(1, 0);
  lcd.print("MOVIENDO A");
  lcd.setCursor(1, 1);
  lcd.print("CERO");

  direccion = false;
  digitalWrite(X_DIR_PIN, direccion);
  while (fc_inic_X == false)
  {
    for (int w = 0; w < 32; w++)
    {
      fc_inic_X = digitalRead(X_MIN_PIN);
      fc_fin_X  = digitalRead(X_MAX_PIN);
      if (fc_fin_X == false and fc_inic_X == false)
      {
        if (w % 2 == 0) //0: par 1:impar
        {
          digitalWrite(X_STEP_PIN, HIGH);
          delayMicroseconds(6);
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
          delayMicroseconds(6);
        }
      }
      else
      {
        digitalWrite(X_STEP_PIN, LOW);
      }
    }
  }
  x = 0;
}

void mover_inicio()
{
  lcd.clear();
  lcd.setCursor(1, 0);
  lcd.print("MOVIENDO A");
  lcd.setCursor(1, 1);
  lcd.print("INICIO");
  lcd.setCursor(1, 2);
  lcd.print("x =");
  lcd.print(" ");

  //x = x_eeprom;
  x_nm = x * 1000000L; //calculo en nanometros, por 1 millon

  if (x < di_X)
  {
    direccion = true;
    digitalWrite(X_DIR_PIN, direccion);
    while (x < di_X)
    {
      for (int w = 0; w < 32; w++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_fin_X == false)
        {
          if (w % 2 == 0) //0: par 1:impar
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(6);
          }
          else
          {
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(6);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
//          lcd.clear();
//          lcd.setCursor(1,0);
//          lcd.print("FINAL DE CARRERA");
//          lcd.setCursor(1,1)
//          lcd.print("ACTIVADO");
//          lcd.setCursor(1,2);
//          lcd.print("x = ");
//          lcd.setCursor(6,2);
//          lcd.print(x);
//          lcd.print(" mm");
        }
      }
      x_nm = x_nm + 147;
      x = x_nm / 1000000;
      lcd.setCursor(6, 2);
      lcd.print(x);
      lcd.print(" mm");
    }
  }
  else
  {
    direccion = false;
    digitalWrite(X_DIR_PIN, direccion);
    while (x > di_X)
    {
      for (int w = 0; w < 32; w++)
      {
        fc_inic_X = digitalRead(X_MIN_PIN);
        fc_fin_X  = digitalRead(X_MAX_PIN);
        if (fc_inic_X == false)
        {
          if (w % 2 == 0) //0: par 1:impar
          {
            digitalWrite(X_STEP_PIN, HIGH);
            delayMicroseconds(6);
          }
          else
          {
            digitalWrite(X_STEP_PIN, LOW);
            delayMicroseconds(6);
          }
        }
        else
        {
          digitalWrite(X_STEP_PIN, LOW);
        }
      }
      x_nm = x_nm - 147;
      x = x_nm / 1000000;
      lcd.setCursor(6, 2);  //columna 6, fila 2
      lcd.print(x);
      lcd.print(" mm");
    }
  }
  x = di_X;
}

void inicio_experimento()
{
  lcd.clear();
  lcd.setCursor(1, 0);
  lcd.print("REALIZANDO");
  lcd.setCursor(1, 1);
  lcd.print("EXPERIMENTO");
  lcd.setCursor(1, 2);
  lcd.print("x =");
  lcd.print(" ");

  if (di_X < df_X)
  {
    direccion = true;
    digitalWrite(X_DIR_PIN, direccion);
  }
  else
  {
    direccion = false;
    digitalWrite(X_DIR_PIN, direccion);
  }

  switch (v)
  {
    case 1: // velocidad = 1 mm/h
      w_final = 2544;
      t_espera = 208;
      break;
    case 2:
      w_final = 1272;
      t_espera = 208;
      break;
    case 3:
      w_final = 848;
      t_espera = 208;
      break;
    case 4:
      w_final = 636;
      t_espera = 208;
      break;
    case 5:
      w_final = 508;
      t_espera = 208;
      break;
    case 6:
      w_final = 424;
      t_espera = 208;
      break;
    case 7:
      w_final = 362;
      t_espera = 208;
      break;
    case 8:
      w_final = 318;
      t_espera = 208;
      break;
    case 9:
      w_final = 282;
      t_espera = 208;
      break;
    case 10:
      w_final = 254;
      t_espera = 208;
      break;
    case 20:
      w_final = 126;
      t_espera = 208;
      break;
    case 30:
      w_final = 84;
      t_espera = 208;
      break;
    case 40:
      w_final = 62;
      t_espera = 208;
      break;
    case 50:
      w_final = 50;
      t_espera = 208;
      break;
    case 60:
      w_final = 42;
      t_espera = 208;
      break;
    case 70:
      w_final = 36;
      t_espera = 208;
      break;
    case 80:
      w_final = 32;
      t_espera = 207;
      break;
    case 90:
      w_final = 32;
      t_espera = 184;
      break;
    default:
      w_final = 32;
      t_espera = 165;
      break;
  }

  //x = x_eeprom;
  x_nm = x * 1000000L; //calculo en nanometros, por 1 millon

  if (x < df_X)
  {
    while (x < df_X)
    {
      if (v < 80)
      {
        for (int w = 0; w < w_final; w++)
        {
          fc_inic_X = digitalRead(X_MIN_PIN);
          fc_fin_X  = digitalRead(X_MAX_PIN);
          if (fc_fin_X == false)
          {
            if (w < 32)
            {
              if (w % 2 == 0) //0: par 1:impar
              {
                digitalWrite(X_STEP_PIN, HIGH);
                delayMicroseconds(t_espera);   //t_espera es el tiempo que tarda un medio micropaso
              }
              else
              {
                digitalWrite(X_STEP_PIN, LOW);  //hay que dividir 416 para estar medio tiempo en HIGH y medio tiempo en LOW
                delayMicroseconds(t_espera);
              }
            }
            else
            {
              digitalWrite(X_STEP_PIN, LOW);
              delayMicroseconds(t_espera);
            }
          }
          else
          {
            digitalWrite(X_STEP_PIN, LOW);
          }
        }
        x_nm = x_nm + 147;
        x = x_nm / 1000000;
        lcd.setCursor(6, 2);
        lcd.print(x);
        lcd.print(" mm");
      }
      else
      {
        for (int w = 0; w < w_final; w++)
        {
          fc_inic_X = digitalRead(X_MIN_PIN);
          fc_fin_X  = digitalRead(X_MAX_PIN);
          if (fc_fin_X == false)
          {
            if (w % 2 == 0) //0: par 1:impar
            {
              digitalWrite(X_STEP_PIN, HIGH);
              delayMicroseconds(t_espera);
            }
            else
            {
              digitalWrite(X_STEP_PIN, LOW);
              delayMicroseconds(t_espera);
            }
          }
          else
          {
            digitalWrite(X_STEP_PIN, LOW);
          }
        }
        x_nm = x_nm + 147;
        x = x_nm / 1000000;
        lcd.setCursor(6, 2);
        lcd.print(x);
        lcd.print(" mm");
      }
    }
  }
  else
  {
    while (x > df_X)
    {
      if (v < 80)
      {
        for (int w = 0; w < w_final; w++)
        {
          fc_inic_X = digitalRead(X_MIN_PIN);
          fc_fin_X  = digitalRead(X_MAX_PIN);
          if (fc_inic_X == false)
          {
            if (w < 32)
            {
              if (w % 2 == 0) //0: par 1:impar
              {
                digitalWrite(X_STEP_PIN, HIGH);
                delayMicroseconds(t_espera);   //t_espera es el tiempo que tarda un medio micropaso
              }
              else
              {
                digitalWrite(X_STEP_PIN, LOW);  //hay que dividir 416 para estar medio tiempo en HIGH y medio tiempo en LOW
                delayMicroseconds(t_espera);
              }
            }
            else
            {
              digitalWrite(X_STEP_PIN, LOW);
              delayMicroseconds(t_espera);
            }
          }
          else
          {
            digitalWrite(X_STEP_PIN, LOW);
          }
        }
        x_nm = x_nm - 147;
        x = x_nm / 1000000;
        lcd.setCursor(6, 2);
        lcd.print(x);
        lcd.print(" mm");
      }
      else
      {
        for (int w = 0; w < w_final; w++)
        {
          fc_inic_X = digitalRead(X_MIN_PIN);
          fc_fin_X  = digitalRead(X_MAX_PIN);
          if (fc_inic_X == false)
          {
            if (w % 2 == 0) //0: par 1:impar
            {
              digitalWrite(X_STEP_PIN, HIGH);
              delayMicroseconds(t_espera);
            }
            else
            {
              digitalWrite(X_STEP_PIN, LOW);
              delayMicroseconds(t_espera);
            }
          }
          else
          {
            digitalWrite(X_STEP_PIN, LOW);
          }
        }
        x_nm = x_nm - 147;
        x = x_nm / 1000000;
        lcd.setCursor(6, 2);
        lcd.print(x);
        lcd.print(" mm");
      }
    }
  }
  x = df_X;
  x_eeprom = x;
  EEPROM.put(DIR_EEP, x_eeprom);
}

void loop ()
{
  switch (estado)
  {
    case 0: // Estado inicial
      comprobar_pos_eep();
      pantalla_inicio();
      estado = 1;
      break;
    case 1: // esperar al pulsador sin hacer nada
      leer_pulso();
      if (pulsador == true)
      {
        menu();
        estado = 2;
      }
      break;
    case 2:
      leer_pulso();
      leer_encoder();
      DefinicionDeVariables();
      break;
    case 3:
      if (x_eeprom < 0)
      {
        reinicio();
        if (x_eeprom != di_X)
        {
          mover_inicio();
          inicio_experimento();
          estado = 0;
        }
        else
        {
          inicio_experimento();
          estado = 0;
        }
      }
      else
      {
        if (x_eeprom != di_X)
        {
          x_eeprom = -1;
          EEPROM.put(DIR_EEP, x_eeprom);
          mover_inicio();
          inicio_experimento();
          estado = 0;
        }
        else
        {
          x_eeprom = -1;
          EEPROM.put(DIR_EEP, x_eeprom);
          inicio_experimento();
          estado = 0;
        }
      }
      break;
    default:
      break;
  }
}
