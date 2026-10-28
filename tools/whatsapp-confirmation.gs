/**
 * Confirmation WhatsApp automatique — Daria & Hermann
 *
 * À coller dans la feuille PRIVÉE des réponses du formulaire :
 *   Extensions → Apps Script → coller ce fichier → Enregistrer.
 *
 * Réglages (Paramètres du projet → Propriétés du script) :
 *   WA_TOKEN      jeton d'accès permanent de l'API WhatsApp Cloud (Meta)
 *   WA_PHONE_ID   « Phone number ID » du numéro expéditeur
 *   WA_TEMPLATE   nom du modèle approuvé (ex. confirmation_reservation)
 *   WA_LANG       langue du modèle (défaut : fr)
 *
 * Puis exécuter une fois installer() pour créer le déclencheur
 * « à l'envoi du formulaire » (Google demande l'autorisation la 1re fois).
 *
 * Le modèle WhatsApp attendu (catégorie « Utilitaire ») a 3 variables :
 *   Bonjour {{1}}, votre réservation pour le mariage de Daria & Hermann est
 *   confirmée (catégorie {{2}}). Votre code : {{3}}.
 *   Rendez-vous le vendredi 18 décembre 2026 — 15h00 Mairie, 16h00 Table des
 *   Élites, Akwa, Douala. Dress code : Terracotta. Présentez ce message à
 *   l'entrée.
 *
 * Le résultat de chaque envoi est noté dans une colonne « WhatsApp » ajoutée
 * à droite des réponses (ENVOYÉ, DOUBLON, ERREUR …).
 */

const COLS = { name: 'Nom &', phone: 'Téléphone', places: 'Nombre de places', code: 'Code', cat: 'Catégorie' };
const STATUS_HEADER = 'WhatsApp';

function installer() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'onReservation')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('onReservation').forSpreadsheet(ss).onFormSubmit().create();
}

/* Déclencheur : une ligne vient d'être ajoutée par le formulaire */
function onReservation(e) {
  const sheet = e.range.getSheet();
  const row = e.range.getRow();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String);
  const col = label => headers.findIndex(h => norm(h).indexOf(norm(label)) === 0);
  const statusCol = ensureStatusColumn(sheet, headers);
  const values = sheet.getRange(row, 1, 1, headers.length).getValues()[0];
  const get = key => { const i = col(COLS[key]); return i < 0 ? '' : String(values[i]).trim(); };

  const phone = normPhone(get('phone'));
  if (!phone) return mark(sheet, row, statusCol, 'NUMÉRO INVALIDE');

  /* unicité : un numéro déjà présent sur une ligne précédente n'est pas reconfirmé */
  const iPhone = col(COLS.phone);
  if (row > 2) {
    const before = sheet.getRange(2, iPhone + 1, row - 2, 1).getValues().map(r => normPhone(r[0]));
    if (before.indexOf(phone) !== -1) return mark(sheet, row, statusCol, 'DOUBLON');
  }

  try {
    sendTemplate(phone, [get('name'), get('cat'), get('code')]);
    mark(sheet, row, statusCol, 'ENVOYÉ ' + Utilities.formatDate(new Date(), 'Africa/Douala', 'dd/MM HH:mm'));
  } catch (err) {
    mark(sheet, row, statusCol, 'ERREUR : ' + String(err.message || err).slice(0, 200));
  }
}

function sendTemplate(phone, params) {
  const p = PropertiesService.getScriptProperties();
  const token = p.getProperty('WA_TOKEN'), phoneId = p.getProperty('WA_PHONE_ID');
  const template = p.getProperty('WA_TEMPLATE'), lang = p.getProperty('WA_LANG') || 'fr';
  if (!token || !phoneId || !template) throw new Error('propriétés WA_* manquantes');
  const res = UrlFetchApp.fetch('https://graph.facebook.com/v21.0/' + phoneId + '/messages', {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true,
    payload: JSON.stringify({
      messaging_product: 'whatsapp',
      to: phone.replace('+', ''),
      type: 'template',
      template: {
        name: template,
        language: { code: lang },
        components: [{ type: 'body', parameters: params.map(t => ({ type: 'text', text: t || '—' })) }]
      }
    })
  });
  if (res.getResponseCode() >= 300) throw new Error(res.getResponseCode() + ' ' + res.getContentText());
}

/* Même règle que le site : 9 chiffres = numéro camerounais */
function normPhone(raw) {
  let d = String(raw).replace(/[\s.\-()\/']/g, '');
  if (d.indexOf('00') === 0) d = '+' + d.slice(2);
  if (/^\d{9}$/.test(d)) d = '+237' + d;
  else if (/^\d{10,15}$/.test(d)) d = '+' + d; /* Sheets peut avoir retiré le « + » */
  return /^\+\d{8,15}$/.test(d) ? d : '';
}

function ensureStatusColumn(sheet, headers) {
  let i = headers.indexOf(STATUS_HEADER);
  if (i === -1) {
    i = headers.length;
    sheet.getRange(1, i + 1).setValue(STATUS_HEADER);
  }
  return i + 1;
}

function mark(sheet, row, col, text) {
  sheet.getRange(row, col).setValue(text);
}

function norm(s) {
  return String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
}

/* Test manuel : envoie le modèle à votre propre numéro */
function testerEnvoi() {
  sendTemplate('+237600000000', ['Test', 'Famille', 'TEST123']);
}
