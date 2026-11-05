/**
 * BDAutos — 25 consultas Aggregation Framework
 * Generado desde app/queries.py. Ejecutar en mongosh tras migrar.
 */

use bdautos;

// ------------------------------------------------------------------
// Consulta 1: Autos 2024+ con al menos 35 mpg
// Obtener los autos de modelo 2024 en adelante con rendimiento de al menos 35 mpg. Mostrar solo descripción, año y rendimiento, ordenados de mayor a menor rendimiento.
// ------------------------------------------------------------------
print("\n=== Consulta 1: Autos 2024+ con al menos 35 mpg ===");
db.cars.aggregate(
  [
    {
      "$match": {
        "year": {
          "$gte": 2024
        },
        "mpg": {
          "$gte": 35
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "descr": 1,
        "year": 1,
        "mpg": 1
      }
    },
    {
      "$sort": {
        "mpg": -1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 2: Europeos 4 cilindros >= 250 hp
// Listar los autos de fabricantes europeos con motor de 4 cilindros y al menos 250 hp, mostrando descripción, país y potencia, ordenados por potencia descendente.
// ------------------------------------------------------------------
print("\n=== Consulta 2: Europeos 4 cilindros >= 250 hp ===");
db.cars.aggregate(
  [
    {
      "$match": {
        "continent.name": "europe",
        "cylinders": 4,
        "horsepower": {
          "$gte": 250
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "descr": 1,
        "pais": "$country.name",
        "horsepower": 1
      }
    },
    {
      "$sort": {
        "horsepower": -1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 3: Japoneses turbo (sufijo Nt)
// Contar cuántos autos de fabricantes japoneses tienen motor turbo, es decir, cuya descripción termina con la cilindrada seguida de 't' (por ejemplo '1.5t').
// ------------------------------------------------------------------
print("\n=== Consulta 3: Japoneses turbo (sufijo Nt) ===");
db.cars.aggregate(
  [
    {
      "$match": {
        "country.name": "japan",
        "descr": {
          "$regex": "\\d+(\\.\\d+)?t$",
          "$options": "i"
        }
      }
    },
    {
      "$count": "japoneses_turbo"
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 4: Ligeros/rápidos o V8 eficientes
// Autos que pesen < 3000 lb y aceleren < 9 s, o tengan 8+ cilindros y rindan al menos 19 mpg.
// ------------------------------------------------------------------
print("\n=== Consulta 4: Ligeros/rápidos o V8 eficientes ===");
db.cars.aggregate(
  [
    {
      "$match": {
        "$or": [
          {
            "weight": {
              "$lt": 3000
            },
            "accel": {
              "$lt": 9
            }
          },
          {
            "cylinders": {
              "$gte": 8
            },
            "mpg": {
              "$gte": 19
            }
          }
        ]
      }
    },
    {
      "$project": {
        "_id": 0,
        "descr": 1,
        "weight": 1,
        "accel": 1,
        "cylinders": 1,
        "mpg": 1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 5: Fabricantes con más de una marca
// Obtener los fabricantes que comercializan más de una marca o línea de modelo, mostrando nombre, país y modelos.
// ------------------------------------------------------------------
print("\n=== Consulta 5: Fabricantes con más de una marca ===");
db.makers.aggregate(
  [
    {
      "$match": {
        "$expr": {
          "$gt": [
            {
              "$size": "$models"
            },
            1
          ]
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "name": 1,
        "pais": "$country.name",
        "modelos": "$models.name"
      }
    },
    {
      "$sort": {
        "name": 1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 6: Marca distinta al grupo fabricante
// Autos cuya marca (model.name) es distinta del nombre de su grupo fabricante (maker.name). Mostrar descripción, marca y fabricante.
// ------------------------------------------------------------------
print("\n=== Consulta 6: Marca distinta al grupo fabricante ===");
db.cars.aggregate(
  [
    {
      "$match": {
        "$expr": {
          "$ne": [
            "$model.name",
            "$maker.name"
          ]
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "descr": 1,
        "marca": "$model.name",
        "fabricante": "$maker.name"
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 7: Stats por país
// Por país: número de autos, rendimiento promedio y potencia promedio (1 decimal), ordenado por número de autos.
// ------------------------------------------------------------------
print("\n=== Consulta 7: Stats por país ===");
db.cars.aggregate(
  [
    {
      "$group": {
        "_id": "$country.name",
        "numAutos": {
          "$sum": 1
        },
        "mpgPromedio": {
          "$avg": "$mpg"
        },
        "hpPromedio": {
          "$avg": "$horsepower"
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "pais": "$_id",
        "numAutos": 1,
        "mpgPromedio": {
          "$round": [
            "$mpgPromedio",
            1
          ]
        },
        "hpPromedio": {
          "$round": [
            "$hpPromedio",
            1
          ]
        }
      }
    },
    {
      "$sort": {
        "numAutos": -1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 8: Stats por grupo fabricante
// Por grupo fabricante: número de autos, marcas distintas con autos y potencia promedio (1 decimal), ordenado por número de autos.
// ------------------------------------------------------------------
print("\n=== Consulta 8: Stats por grupo fabricante ===");
db.cars.aggregate(
  [
    {
      "$group": {
        "_id": {
          "makerId": "$makerId",
          "name": "$maker.name"
        },
        "numAutos": {
          "$sum": 1
        },
        "marcas": {
          "$addToSet": "$model.name"
        },
        "hpPromedio": {
          "$avg": "$horsepower"
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "fabricante": "$_id.name",
        "numAutos": 1,
        "numMarcas": {
          "$size": "$marcas"
        },
        "hpPromedio": {
          "$round": [
            "$hpPromedio",
            1
          ]
        }
      }
    },
    {
      "$sort": {
        "numAutos": -1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 9: Modelos (marcas) por continente
// Contar cuántos modelos (marcas) hay por continente.
// ------------------------------------------------------------------
print("\n=== Consulta 9: Modelos (marcas) por continente ===");
db.makers.aggregate(
  [
    {
      "$unwind": "$models"
    },
    {
      "$group": {
        "_id": "$continent.name",
        "numModelos": {
          "$sum": 1
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "continente": "$_id",
        "numModelos": 1
      }
    },
    {
      "$sort": {
        "numModelos": -1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 10: Rangos de rendimiento (bucket)
// Clasificar autos en rangos de mpg [0,20), [20,25), [25,30), [30,35), [35,40) y 40+, contando cuántos hay y su peso promedio.
// ------------------------------------------------------------------
print("\n=== Consulta 10: Rangos de rendimiento (bucket) ===");
db.cars.aggregate(
  [
    {
      "$bucket": {
        "groupBy": "$mpg",
        "boundaries": [
          0,
          20,
          25,
          30,
          35,
          40
        ],
        "default": "40+",
        "output": {
          "cantidad": {
            "$sum": 1
          },
          "pesoPromedio": {
            "$avg": "$weight"
          }
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "rango": {
          "$switch": {
            "branches": [
              {
                "case": {
                  "$eq": [
                    "$_id",
                    0
                  ]
                },
                "then": "[0,20)"
              },
              {
                "case": {
                  "$eq": [
                    "$_id",
                    20
                  ]
                },
                "then": "[20,25)"
              },
              {
                "case": {
                  "$eq": [
                    "$_id",
                    25
                  ]
                },
                "then": "[25,30)"
              },
              {
                "case": {
                  "$eq": [
                    "$_id",
                    30
                  ]
                },
                "then": "[30,35)"
              },
              {
                "case": {
                  "$eq": [
                    "$_id",
                    35
                  ]
                },
                "then": "[35,40)"
              }
            ],
            "default": "$_id"
          }
        },
        "cantidad": 1,
        "pesoPromedio": {
          "$round": [
            "$pesoPromedio",
            1
          ]
        }
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 11: Top 5 fabricantes por mpg (min 8 autos)
// Los 5 fabricantes con mayor rendimiento promedio, solo con al menos 8 autos registrados.
// ------------------------------------------------------------------
print("\n=== Consulta 11: Top 5 fabricantes por mpg (min 8 autos) ===");
db.cars.aggregate(
  [
    {
      "$group": {
        "_id": "$maker.name",
        "numAutos": {
          "$sum": 1
        },
        "mpgPromedio": {
          "$avg": "$mpg"
        }
      }
    },
    {
      "$match": {
        "numAutos": {
          "$gte": 8
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "fabricante": "$_id",
        "numAutos": 1,
        "mpgPromedio": {
          "$round": [
            "$mpgPromedio",
            1
          ]
        }
      }
    },
    {
      "$sort": {
        "mpgPromedio": -1
      }
    },
    {
      "$limit": 5
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 12: Categoría mpg por continente
// Clasificar cada auto como Alta/Media/Baja según mpg y contar por continente y categoría.
// ------------------------------------------------------------------
print("\n=== Consulta 12: Categoría mpg por continente ===");
db.cars.aggregate(
  [
    {
      "$addFields": {
        "categoria": {
          "$switch": {
            "branches": [
              {
                "case": {
                  "$gte": [
                    "$mpg",
                    30
                  ]
                },
                "then": "Alta"
              },
              {
                "case": {
                  "$and": [
                    {
                      "$gte": [
                        "$mpg",
                        20
                      ]
                    },
                    {
                      "$lt": [
                        "$mpg",
                        30
                      ]
                    }
                  ]
                },
                "then": "Media"
              }
            ],
            "default": "Baja"
          }
        }
      }
    },
    {
      "$group": {
        "_id": {
          "continente": "$continent.name",
          "categoria": "$categoria"
        },
        "cantidad": {
          "$sum": 1
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "continente": "$_id.continente",
        "categoria": "$_id.categoria",
        "cantidad": 1
      }
    },
    {
      "$sort": {
        "continente": 1,
        "categoria": 1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 13: Autos por fabricante (incluye cero)
// Desde la colección makers, obtener cuántos autos tiene registrados cada fabricante (incluidos los que tienen cero).
// ------------------------------------------------------------------
print("\n=== Consulta 13: Autos por fabricante (incluye cero) ===");
db.makers.aggregate(
  [
    {
      "$lookup": {
        "from": "cars",
        "localField": "makerId",
        "foreignField": "makerId",
        "as": "autos"
      }
    },
    {
      "$project": {
        "_id": 0,
        "fabricante": "$name",
        "fullName": 1,
        "numAutos": {
          "$size": "$autos"
        }
      }
    },
    {
      "$sort": {
        "numAutos": -1,
        "fabricante": 1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 14: Modelos del catálogo sin autos
// Modelos del catálogo que no tienen ningún auto registrado.
// ------------------------------------------------------------------
print("\n=== Consulta 14: Modelos del catálogo sin autos ===");
db.makers.aggregate(
  [
    {
      "$unwind": "$models"
    },
    {
      "$lookup": {
        "from": "cars",
        "localField": "models.modelId",
        "foreignField": "modelId",
        "as": "autos"
      }
    },
    {
      "$match": {
        "autos": {
          "$size": 0
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "modelId": "$models.modelId",
        "modelo": "$models.name",
        "fabricante": "$name"
      }
    },
    {
      "$sort": {
        "fabricante": 1,
        "modelo": 1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 15: Top 5 más potentes + fullName
// Para los 5 autos más potentes: descripción, potencia y fullName del fabricante.
// ------------------------------------------------------------------
print("\n=== Consulta 15: Top 5 más potentes + fullName ===");
db.cars.aggregate(
  [
    {
      "$sort": {
        "horsepower": -1
      }
    },
    {
      "$limit": 5
    },
    {
      "$project": {
        "_id": 0,
        "descr": 1,
        "horsepower": 1,
        "fullName": "$maker.fullName"
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 16: Top 3 mpg por continente
// Para cada continente, los 3 autos con mayor rendimiento (descripción y mpg).
// ------------------------------------------------------------------
print("\n=== Consulta 16: Top 3 mpg por continente ===");
db.cars.aggregate(
  [
    {
      "$sort": {
        "continent.name": 1,
        "mpg": -1
      }
    },
    {
      "$group": {
        "_id": "$continent.name",
        "top": {
          "$push": {
            "descr": "$descr",
            "mpg": "$mpg"
          }
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "continente": "$_id",
        "top3": {
          "$slice": [
            "$top",
            3
          ]
        }
      }
    },
    {
      "$sort": {
        "continente": 1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 17: Modelo con más autos por fabricante multi-marca
// Para cada fabricante con más de un modelo, determinar cuál de sus modelos tiene más autos registrados.
// ------------------------------------------------------------------
print("\n=== Consulta 17: Modelo con más autos por fabricante multi-marca ===");
db.cars.aggregate(
  [
    {
      "$group": {
        "_id": {
          "makerId": "$makerId",
          "maker": "$maker.name",
          "model": "$model.name"
        },
        "numAutos": {
          "$sum": 1
        }
      }
    },
    {
      "$group": {
        "_id": {
          "makerId": "$_id.makerId",
          "maker": "$_id.maker"
        },
        "modelos": {
          "$push": {
            "modelo": "$_id.model",
            "numAutos": "$numAutos"
          }
        },
        "numModelos": {
          "$sum": 1
        }
      }
    },
    {
      "$match": {
        "numModelos": {
          "$gt": 1
        }
      }
    },
    {
      "$unwind": "$modelos"
    },
    {
      "$sort": {
        "_id.maker": 1,
        "modelos.numAutos": -1
      }
    },
    {
      "$group": {
        "_id": "$_id",
        "modeloTop": {
          "$first": "$modelos.modelo"
        },
        "numAutos": {
          "$first": "$modelos.numAutos"
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "fabricante": "$_id.maker",
        "modeloTop": 1,
        "numAutos": 1
      }
    },
    {
      "$sort": {
        "fabricante": 1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 18: Porcentaje de autos por continente
// Porcentaje que representa cada continente sobre el total de autos (2 decimales).
// ------------------------------------------------------------------
print("\n=== Consulta 18: Porcentaje de autos por continente ===");
db.cars.aggregate(
  [
    {
      "$group": {
        "_id": "$continent.name",
        "numAutos": {
          "$sum": 1
        }
      }
    },
    {
      "$group": {
        "_id": null,
        "total": {
          "$sum": "$numAutos"
        },
        "items": {
          "$push": {
            "continente": "$_id",
            "numAutos": "$numAutos"
          }
        }
      }
    },
    {
      "$unwind": "$items"
    },
    {
      "$project": {
        "_id": 0,
        "continente": "$items.continente",
        "numAutos": "$items.numAutos",
        "porcentaje": {
          "$round": [
            {
              "$multiply": [
                {
                  "$divide": [
                    "$items.numAutos",
                    "$total"
                  ]
                },
                100
              ]
            },
            2
          ]
        }
      }
    },
    {
      "$sort": {
        "porcentaje": -1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 19: Top 5 que más superan mpg promedio por cilindros
// Los 5 autos que más superan el rendimiento promedio de los autos con su mismo número de cilindros, mostrando ese promedio y la diferencia.
// ------------------------------------------------------------------
print("\n=== Consulta 19: Top 5 que más superan mpg promedio por cilindros ===");
db.cars.aggregate(
  [
    {
      "$setWindowFields": {
        "partitionBy": "$cylinders",
        "output": {
          "mpgPromedioCilindros": {
            "$avg": "$mpg"
          }
        }
      }
    },
    {
      "$addFields": {
        "diferencia": {
          "$subtract": [
            "$mpg",
            "$mpgPromedioCilindros"
          ]
        }
      }
    },
    {
      "$match": {
        "diferencia": {
          "$gt": 0
        }
      }
    },
    {
      "$sort": {
        "diferencia": -1
      }
    },
    {
      "$limit": 5
    },
    {
      "$project": {
        "_id": 0,
        "descr": 1,
        "cylinders": 1,
        "mpg": 1,
        "mpgPromedioCilindros": {
          "$round": [
            "$mpgPromedioCilindros",
            1
          ]
        },
        "diferencia": {
          "$round": [
            "$diferencia",
            1
          ]
        }
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 20: Porcentaje 8+ cilindros por continente
// Por continente: número de autos, cuántos tienen 8+ cilindros y el porcentaje (1 decimal).
// ------------------------------------------------------------------
print("\n=== Consulta 20: Porcentaje 8+ cilindros por continente ===");
db.cars.aggregate(
  [
    {
      "$group": {
        "_id": "$continent.name",
        "numAutos": {
          "$sum": 1
        },
        "con8mas": {
          "$sum": {
            "$cond": [
              {
                "$gte": [
                  "$cylinders",
                  8
                ]
              },
              1,
              0
            ]
          }
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "continente": "$_id",
        "numAutos": 1,
        "con8mas": 1,
        "porcentaje": {
          "$round": [
            {
              "$multiply": [
                {
                  "$divide": [
                    "$con8mas",
                    "$numAutos"
                  ]
                },
                100
              ]
            },
            1
          ]
        }
      }
    },
    {
      "$sort": {
        "continente": 1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 21: Top 10 hp por cada 1000 lb
// Potencia por cada 1000 lb de peso; los 10 autos con mayor valor, junto con su país.
// ------------------------------------------------------------------
print("\n=== Consulta 21: Top 10 hp por cada 1000 lb ===");
db.cars.aggregate(
  [
    {
      "$addFields": {
        "hpPor1000lb": {
          "$multiply": [
            {
              "$divide": [
                "$horsepower",
                "$weight"
              ]
            },
            1000
          ]
        }
      }
    },
    {
      "$sort": {
        "hpPor1000lb": -1
      }
    },
    {
      "$limit": 10
    },
    {
      "$project": {
        "_id": 0,
        "descr": 1,
        "pais": "$country.name",
        "horsepower": 1,
        "weight": 1,
        "hpPor1000lb": {
          "$round": [
            "$hpPor1000lb",
            1
          ]
        }
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 22: Modelos con nombre distinto al fabricante
// Para cada fabricante, mostrar solo los modelos cuyo nombre es distinto al del fabricante; descartar fabricantes sin ninguno.
// ------------------------------------------------------------------
print("\n=== Consulta 22: Modelos con nombre distinto al fabricante ===");
db.makers.aggregate(
  [
    {
      "$project": {
        "_id": 0,
        "fabricante": "$name",
        "modelos": {
          "$filter": {
            "input": "$models",
            "as": "m",
            "cond": {
              "$ne": [
                "$$m.name",
                "$name"
              ]
            }
          }
        }
      }
    },
    {
      "$match": {
        "$expr": {
          "$gt": [
            {
              "$size": "$modelos"
            },
            0
          ]
        }
      }
    },
    {
      "$project": {
        "fabricante": 1,
        "modelos": "$modelos.name"
      }
    },
    {
      "$sort": {
        "fabricante": 1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 23: Facet: continente, cilindros y stats mpg
// En una sola consulta: (a) autos por continente, (b) autos por cilindros, (c) min/max/avg globales de mpg.
// ------------------------------------------------------------------
print("\n=== Consulta 23: Facet: continente, cilindros y stats mpg ===");
db.cars.aggregate(
  [
    {
      "$facet": {
        "porContinente": [
          {
            "$group": {
              "_id": "$continent.name",
              "numAutos": {
                "$sum": 1
              }
            }
          },
          {
            "$sort": {
              "numAutos": -1
            }
          },
          {
            "$project": {
              "_id": 0,
              "continente": "$_id",
              "numAutos": 1
            }
          }
        ],
        "porCilindros": [
          {
            "$group": {
              "_id": "$cylinders",
              "numAutos": {
                "$sum": 1
              }
            }
          },
          {
            "$sort": {
              "_id": 1
            }
          },
          {
            "$project": {
              "_id": 0,
              "cylinders": "$_id",
              "numAutos": 1
            }
          }
        ],
        "statsMpg": [
          {
            "$group": {
              "_id": null,
              "min": {
                "$min": "$mpg"
              },
              "max": {
                "$max": "$mpg"
              },
              "avg": {
                "$avg": "$mpg"
              }
            }
          },
          {
            "$project": {
              "_id": 0,
              "min": 1,
              "max": 1,
              "avg": {
                "$round": [
                  "$avg",
                  1
                ]
              }
            }
          }
        ]
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 24: Ranking potencia autos alemanes (top 5)
// Asignar a cada auto alemán su posición por potencia dentro de su país y mostrar los 5 primeros.
// ------------------------------------------------------------------
print("\n=== Consulta 24: Ranking potencia autos alemanes (top 5) ===");
db.cars.aggregate(
  [
    {
      "$match": {
        "country.name": "germany"
      }
    },
    {
      "$setWindowFields": {
        "partitionBy": "$country.name",
        "sortBy": {
          "horsepower": -1
        },
        "output": {
          "posicion": {
            "$rank": {}
          }
        }
      }
    },
    {
      "$match": {
        "posicion": {
          "$lte": 5
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "posicion": 1,
        "descr": 1,
        "horsepower": 1,
        "pais": "$country.name"
      }
    },
    {
      "$sort": {
        "posicion": 1
      }
    }
  ]
);

// ------------------------------------------------------------------
// Consulta 25: Auto más eficiente por fabricante europeo
// Para cada fabricante europeo, su auto más eficiente (mayor mpg).
// ------------------------------------------------------------------
print("\n=== Consulta 25: Auto más eficiente por fabricante europeo ===");
db.cars.aggregate(
  [
    {
      "$match": {
        "continent.name": "europe"
      }
    },
    {
      "$sort": {
        "maker.name": 1,
        "mpg": -1
      }
    },
    {
      "$group": {
        "_id": "$maker.name",
        "descr": {
          "$first": "$descr"
        },
        "mpg": {
          "$first": "$mpg"
        },
        "fullName": {
          "$first": "$maker.fullName"
        }
      }
    },
    {
      "$project": {
        "_id": 0,
        "fabricante": "$_id",
        "fullName": 1,
        "descr": 1,
        "mpg": 1
      }
    },
    {
      "$sort": {
        "fabricante": 1
      }
    }
  ]
);

