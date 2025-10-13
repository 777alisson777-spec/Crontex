
/* Tabs + grade dinâmica - Versão Simplificada e Funcional */
(function () {
  "use strict";

  // ========== CONFIGURAÇÃO DAS ABAS ==========
  function initTabs() {
    const tabs = document.querySelectorAll('.tabs .tab');
    const panels = document.querySelectorAll('.tab-panel');

    tabs.forEach(tab => {
      tab.addEventListener('click', function() {
        const targetTab = this.getAttribute('data-tab');
        
        // Atualizar tabs
        tabs.forEach(t => {
          t.classList.remove('is-active');
          t.setAttribute('aria-selected', 'false');
        });
        this.classList.add('is-active');
        this.setAttribute('aria-selected', 'true');

        // Atualizar panels
        panels.forEach(panel => {
          const panelTab = panel.getAttribute('data-tab');
          if (panelTab === targetTab) {
            panel.hidden = false;
            panel.classList.add('is-active');
          } else {
            panel.hidden = true;
            panel.classList.remove('is-active');
          }
        });
      });
    });
  }

  // ========== ADIÇÃO DINÂMICA DE CAMPOS ==========
  function initDynamicAdd() {
    document.querySelectorAll('.dynamic-add').forEach(button => {
      button.addEventListener('click', function(e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('data-add');
        const templateId = this.getAttribute('data-template');
        const target = document.querySelector(targetId);
        const template = document.querySelector(templateId);

        if (!target || !template) return;

        const newIndex = target.children.length + 1;
        const clone = template.content.cloneNode(true);

        // Atualizar todos os names com o índice
        clone.querySelectorAll('[name]').forEach(input => {
          const name = input.getAttribute('name').replace('__idx__', newIndex);
          input.setAttribute('name', name);
        });

        target.appendChild(clone);

        // Inicializar token input se for campo de valores
        const valuesInput = clone.querySelector('input[name*="var_values"]');
        if (valuesInput) {
          initTokenInput(valuesInput);
        }
      });
    });
  }

  // ========== TOKEN INPUT (CHIPS) ==========
  function initTokenInput(input) {
    if (input._tokenInitialized) return;
    input._tokenInitialized = true;

    const wrapper = document.createElement('div');
    wrapper.className = 'token-input-wrapper';
    wrapper.style.cssText = `
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 4px;
      min-height: 38px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 4px;
    `;

    const tokensContainer = document.createElement('div');
    tokensContainer.className = 'tokens-container';
    tokensContainer.style.cssText = `
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      flex: 1;
    `;

    // Mover input para dentro do wrapper
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(tokensContainer);
    wrapper.appendChild(input);

    input.style.cssText = `
      border: none;
      outline: none;
      flex: 1;
      min-width: 60px;
      padding: 4px;
    `;

    let tokens = [];

    function renderTokens() {
      tokensContainer.innerHTML = '';
      
      tokens.forEach((token, index) => {
        const tokenEl = document.createElement('span');
        tokenEl.className = 'token';
        tokenEl.style.cssText = `
          background: #e9ecef;
          border: 1px solid #ced4da;
          border-radius: 12px;
          padding: 2px 8px;
          font-size: 12px;
          display: flex;
          align-items: center;
          gap: 4px;
        `;

        const tokenText = document.createTextNode(token);
        tokenEl.appendChild(tokenText);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.innerHTML = '×';
        removeBtn.style.cssText = `
          background: none;
          border: none;
          cursor: pointer;
          font-size: 14px;
          padding: 0;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
        `;
        
        removeBtn.addEventListener('click', () => {
          tokens.splice(index, 1);
          renderTokens();
          updateGrade();
        });

        tokenEl.appendChild(removeBtn);
        tokensContainer.appendChild(tokenEl);
      });

      // Atualizar valor do input hidden
      input.value = tokens.join(', ');
    }

    function addToken(text) {
      const newTokens = text.split(/[,;\t\n\r\s]+/)
        .map(t => t.trim())
        .filter(t => t && !tokens.includes(t));
      
      tokens.push(...newTokens);
      renderTokens();
    }

    // Inicializar com valores existentes
    if (input.value) {
      addToken(input.value);
    }

    input.addEventListener('keydown', function(e) {
      if (['Enter', 'Tab', ','].includes(e.key)) {
        e.preventDefault();
        if (input.value.trim()) {
          addToken(input.value);
          input.value = '';
        }
      } else if (e.key === 'Backspace' && !input.value && tokens.length > 0) {
        tokens.pop();
        renderTokens();
        updateGrade();
      }
    });

    input.addEventListener('blur', function() {
      if (input.value.trim()) {
        addToken(input.value);
        input.value = '';
        updateGrade();
      }
    });
  }

  function initAllTokenInputs() {
    // Campo fixo inicial
    const firstValuesInput = document.getElementById('var-values-0');
    if (firstValuesInput) initTokenInput(firstValuesInput);

    // Campos dinâmicos existentes
    document.querySelectorAll('#variations-def input[name*="var_values"]').forEach(initTokenInput);
  }

  // ========== SISTEMA DE GRADE ==========
  function getAllVariations() {
    const variations = [];

    // Primeira linha fixa
    const firstName = document.getElementById('var-name-0');
    const firstValues = document.getElementById('var-values-0');
    const firstAxis = document.getElementById('var-axis-0');

    if (firstName && firstValues && firstAxis) {
      const name = firstName.value.trim();
      const values = firstValues.value.split(',').map(v => v.trim()).filter(v => v);
      const axis = firstAxis.value;

      if (name && values.length > 0) {
        variations.push({ name, values, axis });
      }
    }

    // Linhas dinâmicas
    document.querySelectorAll('#variations-def [data-row]').forEach(row => {
      const nameInput = row.querySelector('input[name*="var_name"]');
      const valuesInput = row.querySelector('input[name*="var_values"]');
      const axisSelect = row.querySelector('select[name*="var_axis"]');

      if (nameInput && valuesInput && axisSelect) {
        const name = nameInput.value.trim();
        const values = valuesInput.value.split(',').map(v => v.trim()).filter(v => v);
        const axis = axisSelect.value;

        if (name && values.length > 0) {
          variations.push({ name, values, axis });
        }
      }
    });

    return variations;
  }

  function generateCombinations(arrays) {
    if (arrays.length === 0) return [[]];
    
    const result = [];
    const first = arrays[0];
    const rest = generateCombinations(arrays.slice(1));
    
    first.forEach(item => {
      rest.forEach(combination => {
        result.push([item].concat(combination));
      });
    });
    
    return result;
  }

  function updateGrade() {
    const variations = getAllVariations();
    const gradeTable = document.getElementById('grade-table');
    
    if (!gradeTable) return;

    if (variations.length === 0) {
      gradeTable.innerHTML = '<p class="alert info">Adicione variações para gerar a grade</p>';
      return;
    }

    // Separar variações por eixo
    const rowVariations = variations.filter(v => v.axis === 'row');
    const colVariations = variations.filter(v => v.axis === 'col');

    // Gerar combinações
    const rowCombinations = rowVariations.length > 0 ? 
      generateCombinations(rowVariations.map(v => v.values)) : 
      [['Único']];
    
    const colCombinations = colVariations.length > 0 ? 
      generateCombinations(colVariations.map(v => v.values)) : 
      [['Único']];

    // Criar tabela
    let html = '<table class="table grade-table" style="width: auto; border-collapse: collapse;">';
    
    // Cabeçalho
    html += '<thead><tr>';
    html += `<th style="border: 1px solid #ddd; padding: 8px; background: #f8f9fa;">${rowVariations.map(v => v.name).join(' / ') || 'Variação'}</th>`;
    
    colCombinations.forEach(combination => {
      html += `<th style="border: 1px solid #ddd; padding: 8px; background: #f8f9fa;">${combination.join(' / ')}</th>`;
    });
    
    html += '</tr></thead>';

    // Corpo
    html += '<tbody>';
    rowCombinations.forEach(rowCombo => {
      html += '<tr>';
      html += `<th style="border: 1px solid #ddd; padding: 8px; background: #f8f9fa;">${rowCombo.join(' / ')}</th>`;
      
      colCombinations.forEach(colCombo => {
        const rowKey = rowCombo.join('_');
        const colKey = colCombo.join('_');
        html += `<td style="border: 1px solid #ddd; padding: 4px;">`;
        html += `<input type="number" name="grade_qty[${rowKey}][${colKey}]" 
                 class="input" style="width: 80px; text-align: center;" 
                 min="0" step="1" placeholder="0">`;
        html += '</td>';
      });
      
      html += '</tr>';
    });
    html += '</tbody></table>';

    gradeTable.innerHTML = html;
  }

  function initGradeSystem() {
    const generateBtn = document.getElementById('btn-generate-grade');
    
    if (generateBtn) {
      generateBtn.addEventListener('click', function(e) {
        e.preventDefault();
        updateGrade();
      });
    }

    // Atualização automática
    const gradeContainer = document.getElementById('grade-from-variations');
    if (gradeContainer) {
      gradeContainer.addEventListener('input', function(e) {
        const target = e.target;
        if (target.matches('input[name*="var_"], select[name*="var_"], #var-name-0, #var-values-0, #var-axis-0')) {
          clearTimeout(this._updateTimeout);
          this._updateTimeout = setTimeout(updateGrade, 300);
        }
      });
    }

    // Gerar grade inicial se houver dados
    setTimeout(updateGrade, 1000);
  }

  // ========== INICIALIZAÇÃO ==========
  document.addEventListener('DOMContentLoaded', function() {
    // Gerar UUID único para o formulário
    const formUid = document.querySelector('input[name="form_uid"]');
    if (formUid && !formUid.value) {
      formUid.value = 'form_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Inicializar todos os sistemas
    initTabs();
    initDynamicAdd();
    initAllTokenInputs();
    initGradeSystem();
  });

})();
