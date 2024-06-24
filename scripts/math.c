#include <math.h>

  __declspec(dllexport) float acosf(float _X) { return ((float)acos((double)_X)); }
  __declspec(dllexport) float asinf(float _X) { return ((float)asin((double)_X)); }
  __declspec(dllexport) float atanf(float _X) { return ((float)atan((double)_X)); }
  __declspec(dllexport) float atan2f(float _X,float _Y) { return ((float)atan2((double)_X,(double)_Y)); }
  __declspec(dllexport) float ceilf(float _X) { return ((float)ceil((double)_X)); }
  __declspec(dllexport) float cosf(float _X) { return ((float)cos((double)_X)); }
  __declspec(dllexport) float coshf(float _X) { return ((float)cosh((double)_X)); }
  __declspec(dllexport) float expf(float _X) { return ((float)exp((double)_X)); }
  __declspec(dllexport) float floorf(float _X) { return ((float)floor((double)_X)); }
  __declspec(dllexport) float fmodf(float _X,float _Y) { return ((float)fmod((double)_X,(double)_Y)); }
  __declspec(dllexport) float logf(float _X) { return ((float)log((double)_X)); }
  __declspec(dllexport) float log10f(float _X) { return ((float)log10((double)_X)); }
  __declspec(dllexport) float modff(float _X,float *_Y) {
    double _Di,_Df = modf((double)_X,&_Di);
    *_Y = (float)_Di;
    return ((float)_Df);
  }
  __declspec(dllexport) float powf(float _X,float _Y) { return ((float)pow((double)_X,(double)_Y)); }
  __declspec(dllexport) float sinf(float _X) { return ((float)sin((double)_X)); }
  __declspec(dllexport) float sinhf(float _X) { return ((float)sinh((double)_X)); }
  __declspec(dllexport) float sqrtf(float _X) { return ((float)sqrt((double)_X)); }
  __declspec(dllexport) float tanf(float _X) { return ((float)tan((double)_X)); }
  __declspec(dllexport) float tanhf(float _X) { return ((float)tanh((double)_X)); }
