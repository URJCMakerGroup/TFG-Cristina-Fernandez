// Biblioteca de la pantalla LCD
#include <LiquidCrystal.h>
LiquidCrystal lcd(16, 17, 23, 25, 27, 29);

//Pins de la shield
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
#define X_MIN_PIN 3         // PIN para el fin de carrera colocado al inicio del recorrido
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

//variables internas
bool btn_en1, btn_en2, btn_enc, btn_en1_prev, btn_en2_prev ;       //variables de lectura directa del encoder
bool fc_inic_X, fc_fin_X = true;                                   //variables de lectura de los fin de carrera
bool direccion = false;                                            //variables para escribir los motores
bool derecha, izquierda, pulsador = false;                         // variables de lectura del encoder interpretadas
int volatile estado, estado_ant = 0;                               // Variables del estado (valores de 0 a 5)
int fila, columna = 0;                                             // Variable de fila en la pantalla lcd
int i, j = 0;                                                      // contador de medios micropasos
long di_X, df_X = 0L;                                              // variables del ensayo (distancia inicial, distancia final, velocidad)
long x = 0L ;                                                      // variable de la distancia puntual (en micras)
int t, tiempo, v, avance = 1;                                      // variable para definir la velocidad
int l = 400;                                                       // l es la longitud del husillo, por lo que se trata de la distancia máxima que se puede llevar a cabo

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
  lcd.createChar(0, empty);   // 0: numero de carécter; empty: matriz que contiene los pixeles del carácter
  lcd.createChar(1,  full);   // 1: numero de carécter; full: matriz que contiene los pixeles del carácter
  lcd.createChar(2, micro);   // 2: numero de carécter; micro: matriz que contiene los pixeles del carácter

  lcd.clear();
  lcd.setCursor(2, 0);    // posiciona el cursor en la columna 1 fila 0
  lcd.print("ENSAYO DE MODELO");
  lcd.setCursor(3, 1);    // posiciona el cursor en la columna 1 fila 1
  lcd.print("ANALOGO SIMPLE");
  lcd.setCursor(0, 3);    // posiciona el cursor en la columna 1 fila 3
  lcd.print("Iniciar Experimento");
}

/////////////////ESTADOS/////////////////

/////////////////Estado 0: INICIO/////////////////
void inicio()
{
  avance = 0;
  if (pulsador == true)
  {
    estado = 1;
    estado_ant = 0;

    fila, columna = 0;
    di_X = 0L;
    df_X = 0L;
    tiempo = 1;
    v = 1;
    x = 0L;

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
    lcd.print("inicio del experimento");
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
}

/////////////////Estado 1: DEFINICIÓN DE VARIABLES/////////////////
void DefinicionDeVariables()
{
  avance = 0;
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
          if (derecha == true and di_X + 1 < l)
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
          if (derecha == true and di_X + 10 < l)
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
          if (derecha == true and di_X + 100 < l)
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
          if (derecha == true and df_X + 1 < l)
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
          if (derecha == true and df_X + 10 < l)
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
          if (derecha == true and df_X + 100 < l)
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
        estado = 2;
        estado_ant = 1;
        di_X = di_X * 1000L;
        df_X = df_X * 1000L;

        lcd.clear();
        lcd.setCursor(1, 0);
        lcd.print("PREPARANDO");
        lcd.setCursor(1, 1);
        lcd.print("EXPERIMENTO...");
        tiempo = 1;
        avance = 375;
        j = 0;
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

/////////////////Estado 2: PREPARACIÓN/////////////////
void preparacion()
{
  
}

/////////////////Estado 3: ACCIÓN/////////////////
void accion()
{
  
}

///////////////////////////////////////////////////
void loop()
{
  
}
