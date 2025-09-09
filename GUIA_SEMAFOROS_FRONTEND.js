/* 
===================================================================
🎯 GUÍA DE IMPLEMENTACIÓN DE SEMÁFOROS EN EL FRONTEND
===================================================================

Los semáforos ya están implementados en el backend en estos endpoints:
- /api/db/deposits/by-plant
- /api/db/deposits/by-machine

Cada depósito ahora incluye un objeto "semaforo_docs" con esta información:
*/

// EJEMPLO DE RESPUESTA DEL BACKEND:
const depositoEjemplo = {
  "deposit_id": "39346522",
  "user_name": "199, RTO 199",
  "composicion_esperado": "ECR",  // E=efectivo, C=cheques, R=retenciones
  "total_cheques": 2,
  "total_retenciones": 1,
  "semaforo_docs": {
    "cheques_esperados": true,        // Se esperan cheques según API
    "retenciones_esperadas": true,    // Se esperan retenciones según API  
    "cheques_cargados": true,         // Hay cheques cargados
    "retenciones_cargadas": true,     // Hay retenciones cargadas
    "cheques_pendientes": false,      // false porque ya están cargados
    "retenciones_pendientes": false,  // false porque ya están cargadas
    "docs_completos": true,           // Todos los docs esperados están cargados
    "tiene_docs_esperados": true      // Hay documentos esperados
  }
}

// ===================================================================
// 🎨 IMPLEMENTACIÓN EN VUE.JS / JAVASCRIPT
// ===================================================================

// 1. FUNCIÓN PARA OBTENER EL COLOR DEL SEMÁFORO
function getSemaforoColor(semaforo) {
  if (!semaforo.tiene_docs_esperados) {
    return 'gray';     // Sin documentos esperados
  }
  
  if (semaforo.docs_completos) {
    return 'green';    // Documentos completos ✅
  }
  
  return 'yellow';     // Documentos pendientes ⚠️
}

// 2. FUNCIÓN PARA OBTENER EL ICONO DEL SEMÁFORO
function getSemaforoIcon(semaforo) {
  if (!semaforo.tiene_docs_esperados) {
    return '⚪';  // Sin docs esperados
  }
  
  if (semaforo.docs_completos) {
    return '✅';  // Completo
  }
  
  return '⚠️';   // Pendiente
}

// 3. FUNCIÓN PARA OBTENER EL MENSAJE DEL SEMÁFORO
function getSemaforoMessage(semaforo) {
  if (!semaforo.tiene_docs_esperados) {
    return 'Sin documentos esperados';
  }
  
  if (semaforo.docs_completos) {
    return 'Documentos completos';
  }
  
  let pendientes = [];
  if (semaforo.cheques_pendientes) {
    pendientes.push('cheques');
  }
  if (semaforo.retenciones_pendientes) {
    pendientes.push('retenciones');
  }
  
  return `Faltan: ${pendientes.join(', ')}`;
}

// ===================================================================
// 🎨 COMPONENTE VUE EJEMPLO
// ===================================================================

const SemaforoComponent = {
  props: ['semaforo'],
  template: `
    <div class="semaforo" :class="semaforoClass">
      <span class="semaforo-icon">{{ semaforoIcon }}</span>
      <span class="semaforo-text">{{ semaforoMessage }}</span>
      
      <!-- Indicadores detallados -->
      <div class="semaforo-details" v-if="semaforo.tiene_docs_esperados">
        <span v-if="semaforo.cheques_esperados" 
              :class="{'complete': semaforo.cheques_cargados, 'pending': !semaforo.cheques_cargados}">
          📄 Cheques
        </span>
        <span v-if="semaforo.retenciones_esperadas"
              :class="{'complete': semaforo.retenciones_cargadas, 'pending': !semaforo.retenciones_cargadas}">
          🧾 Retenciones  
        </span>
      </div>
    </div>
  `,
  computed: {
    semaforoClass() {
      return `semaforo-${getSemaforoColor(this.semaforo)}`;
    },
    semaforoIcon() {
      return getSemaforoIcon(this.semaforo);
    },
    semaforoMessage() {
      return getSemaforoMessage(this.semaforo);
    }
  }
}

// ===================================================================
// 🎨 CSS PARA LOS SEMÁFOROS
// ===================================================================

const css = `
.semaforo {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.semaforo-green {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.semaforo-yellow {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.semaforo-gray {
  background-color: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
}

.semaforo-icon {
  margin-right: 4px;
}

.semaforo-details {
  margin-left: 8px;
  display: flex;
  gap: 4px;
}

.semaforo-details .complete {
  color: #28a745;
}

.semaforo-details .pending {
  color: #ffc107;
  font-weight: bold;
}

/* Para las tablas */
.table-docs-column {
  min-width: 150px;
}

/* Indicador en la cabecera de la tabla */
.docs-header {
  display: flex;
  align-items: center;
  gap: 4px;
}

.docs-summary {
  font-size: 10px;
  background: #007bff;
  color: white;
  padding: 2px 4px;
  border-radius: 8px;
}
`;

// ===================================================================
// 🚀 EJEMPLO DE USO EN LA TABLA
// ===================================================================

// En tu componente de tabla de Vue:
const TablaDepositos = {
  data() {
    return {
      depositos: [],
      resumenDocs: {
        pendientes: 0,
        completos: 0,
        sinDocs: 0
      }
    }
  },
  methods: {
    async loadDepositos(fecha) {
      const response = await fetch(`/api/db/deposits/by-plant?date=${fecha}`);
      const data = await response.json();
      
      this.depositos = [];
      this.resumenDocs = { pendientes: 0, completos: 0, sinDocs: 0 };
      
      // Procesar todas las plantas
      Object.values(data.plants).forEach(plant => {
        plant.deposits.forEach(deposit => {
          this.depositos.push(deposit);
          
          // Contar para el resumen
          const semaforo = deposit.semaforo_docs;
          if (!semaforo.tiene_docs_esperados) {
            this.resumenDocs.sinDocs++;
          } else if (semaforo.docs_completos) {
            this.resumenDocs.completos++;
          } else {
            this.resumenDocs.pendientes++;
          }
        });
      });
    }
  },
  template: `
    <div>
      <!-- Resumen en la cabecera -->
      <div class="docs-summary-header">
        <span class="badge badge-warning" v-if="resumenDocs.pendientes > 0">
          ⚠️ {{ resumenDocs.pendientes }} con docs pendientes
        </span>
        <span class="badge badge-success" v-if="resumenDocs.completos > 0">
          ✅ {{ resumenDocs.completos }} completos
        </span>
      </div>
      
      <!-- Tabla -->
      <table class="table">
        <thead>
          <tr>
            <th>Depósito</th>
            <th>Monto</th>
            <th class="docs-header">
              📄 Docs
              <span class="docs-summary" v-if="resumenDocs.pendientes > 0">
                {{ resumenDocs.pendientes }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="deposit in depositos" :key="deposit.deposit_id">
            <td>{{ deposit.deposit_id }}</td>
            <td>{{ deposit.total_amount }}</td>
            <td class="table-docs-column">
              <semaforo-component :semaforo="deposit.semaforo_docs" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `
}

// ===================================================================
// 🎯 BENEFICIOS PARA EL USUARIO
// ===================================================================

/*
✅ ANTES: El operador tenía que hacer clic en cada registro para ver si había documentos

⚠️ AHORA: El operador ve inmediatamente:
  - 🟢 Verde: Documentos completos, todo OK
  - 🟡 Amarillo: Faltan documentos, necesita revisar  
  - ⚪ Gris: No se esperan documentos

🚀 MEJORAS DE PRODUCTIVIDAD:
  - Vista rápida del estado de toda la tabla
  - Priorización automática (atender primero los amarillos)
  - Contador en tiempo real de pendientes
  - No necesidad de hacer clic para verificar estado
*/
