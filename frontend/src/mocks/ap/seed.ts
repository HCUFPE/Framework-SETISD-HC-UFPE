/**
 * Carga inicial FICTÍCIA do Sistema AP (somente para desenvolvimento e validação com usuários).
 *
 * Todos os nomes, prontuários, números de solicitação e funcionários foram inventados para este
 * mock e não correspondem a pessoas ou registros reais. As datas são relativas ao momento da carga.
 *
 * Os domínios (status do item, origem, exames, unidades e especialidades) usam APENAS valores
 * listados em `data/dicionario_dados.md`.
 */
import { ETAPAS, EXAMES_AGHU, fluxoDoCaso } from '../../constants/ap';
import { chaveExame, resumirExamesDoGrupo, resumoMaterial } from '../../helpers/aghu';
import type {
  AmostraAghu,
  AuditLog,
  CasoAp,
  CasoEtapa,
  ConferenciaRecebimento,
  Devolucao,
  EtapaCodigo,
  ExameIhq,
  HistoricoCaso,
  ItemMaterial,
  NaoConformidade,
  OrigemAtendimento,
  RegistroEtapa,
  Responsavel,
  SolicitacaoAghu,
  StatusCaso,
  TipoCasoPrincipal,
  TipoExame,
} from '../../types/ap';

/** Estrutura do "banco" em memória. */
export interface MockDb {
  solicitacoes: SolicitacaoAghu[];
  /** Casos sem as relações compostas (conferência, não conformidades, devoluções). */
  casos: CasoAp[];
  conferencias: ConferenciaRecebimento[];
  naoConformidades: NaoConformidade[];
  devolucoes: Devolucao[];
  auditoria: AuditLog[];
  aghuDisponivel: boolean;
  sequencias: Record<'historico' | 'conferencia' | 'naoConformidade' | 'devolucao' | 'auditoria', number>;
}

// ---------------------------------------------------------------------------
// Pessoas fictícias
// ---------------------------------------------------------------------------

/** Funcionários fictícios do SAP. */
export const EQUIPE = {
  recepcao: { login: 'joana.valenca', nome: 'Joana Valença' },
  recepcao2: { login: 'italo.brennand', nome: 'Ítalo Brennand' },
  macroscopia: { login: 'elisa.matarazzo', nome: 'Elisa Matarazzo' },
  processamento: { login: 'rui.peixoto', nome: 'Rui Peixoto' },
  ihq: { login: 'nadia.quintela', nome: 'Nádia Quintela' },
  citotecnico: { login: 'cecilia.prates', nome: 'Cecília Prates' },
  residente: { login: 'danilo.ventura', nome: 'Dr. Danilo Ventura' },
  residente2: { login: 'bianca.saldanha', nome: 'Dra. Bianca Saldanha' },
  patologista: { login: 'selma.aranha', nome: 'Dra. Selma Aranha' },
  patologista2: { login: 'julio.paranhos', nome: 'Dr. Júlio Paranhos' },
  arquivo: { login: 'wagner.amorim', nome: 'Wagner Amorim' },
  chefia: { login: 'regina.marinho', nome: 'Dra. Regina Marinho' },
} satisfies Record<string, Responsavel>;

interface PacienteFicticio {
  nome: string;
  prontuario: string;
  nascimento: string;
}

const P = {
  odete: { nome: 'ODETE MARQUES VALADARES', prontuario: '2301145', nascimento: '1957-04-18' },
  gerson: { nome: 'GERSON TAVORA LINHARES', prontuario: '2287430', nascimento: '1969-11-02' },
  iracema: { nome: 'IRACEMA BRAGANÇA FONTES', prontuario: '2315528', nascimento: '1972-06-25' },
  wilson: { nome: 'WILSON ALCÂNTARA REIS', prontuario: '2199803', nascimento: '1951-01-30' },
  neide: { nome: 'NEIDE CAMPELO SARMENTO', prontuario: '2340017', nascimento: '1963-09-12' },
  telma: { nome: 'TELMA FIGUEIRA LOBO', prontuario: '2352291', nascimento: '1978-03-07' },
  ednaldo: { nome: 'EDNALDO PIMENTA CASTRO', prontuario: '2276654', nascimento: '1984-12-19' },
  zuleide: { nome: 'ZULEIDE MOTA GUSMÃO', prontuario: '2368140', nascimento: '1995-08-21' },
  valter: { nome: 'VALTER CORDEIRO BASTOS', prontuario: '2241976', nascimento: '1960-05-14' },
  mirtes: { nome: 'MIRTES ALENCAR PAIXÃO', prontuario: '2374405', nascimento: '1968-02-09' },
  jurandir: { nome: 'JURANDIR VILELA SOBRAL', prontuario: '2229518', nascimento: '1956-10-03' },
  cleonice: { nome: 'CLEONICE AMARAL TEIXEIRA', prontuario: '2318862', nascimento: '1949-07-28' },
  ademir: { nome: 'ADEMIR PORTELA RIBAS', prontuario: '2381037', nascimento: '1966-04-11' },
  socorro: { nome: 'SOCORRO MACHADO LEAL', prontuario: '2290715', nascimento: '1975-12-01' },
  rosimere: { nome: 'ROSIMERE TOLEDO BRITO', prontuario: '2333409', nascimento: '1988-06-16' },
  marinalva: { nome: 'MARINALVA COUTO RANGEL', prontuario: '2386652', nascimento: '1991-01-23' },
  doralice: { nome: 'DORALICE PIRES SALGADO', prontuario: '2254381', nascimento: '1980-09-30' },
  gloria: { nome: 'GLÓRIA PASSOS TRINDADE', prontuario: '2362278', nascimento: '1970-03-15' },
  leonardo: { nome: 'LEONARDO AQUINO BARRETO', prontuario: '2347793', nascimento: '1958-08-08' },
  aurelio: { nome: 'AURÉLIO MATOS REBOUÇAS', prontuario: '2390114', nascimento: '1962-11-27' },
  erivaldo: { nome: 'ERIVALDO SANTANA MENDONÇA', prontuario: '2391560', nascimento: '1954-02-04' },
  jandira: { nome: 'JANDIRA NOVAES COELHO', prontuario: '2392007', nascimento: '1983-05-19' },
  osvaldo: { nome: 'OSVALDO FERRAZ LIMEIRA', prontuario: '2392843', nascimento: '1965-10-10' },
  gilvan: { nome: 'GILVAN ESTEVES PRADO', prontuario: '2389476', nascimento: '1977-07-02' },
  mariaGracas: { nome: 'MARIA DAS GRAÇAS DE ALBUQUERQUE CAVALCANTI DOS SANTOS', prontuario: '2393318', nascimento: '1961-03-22' },
  lucineide: { nome: 'LUCINEIDE FARIAS DO NASCIMENTO', prontuario: '2393402', nascimento: '1979-09-05' },
} satisfies Record<string, PacienteFicticio>;

/** Especialidades solicitantes (valores do dicionário do AGHU). */
const MED = {
  gastro: { especialidade: 'GASTROENTEROLOGIA' },
  cirurgia: { especialidade: 'CIRURGIA GERAL' },
  gineco: { especialidade: 'GINECOLOGIA' },
  uro: { especialidade: 'UROLOGIA' },
  mastologia: { especialidade: 'ONCOLOGIA - MASTOLOGIA' },
  cabecaPescoco: { especialidade: 'CIRURGIA DE CABECA E PESCOCO' },
  clinica: { especialidade: 'CLINICA MEDICA' },
  dermato: { especialidade: 'DERMATOLOGIA' },
  toracica: { especialidade: 'CIRURGIA TORACICA' },
  externo: { especialidade: '' },
};

/** Sigla padrão do exame do AGHU por tipo do SAP. */
const SIGLA_PADRAO: Record<TipoExame, string> = {
  HP: 'APECR',
  CG: 'CITOP',
  CCV: 'CCVM',
  CO: 'CONGE',
  REVISAO: 'REV',
  IHQ: 'IMUHI',
};

/** Unidades usadas no seed (valores do dicionário do AGHU). */
const U = {
  ambGastro: 'GASTROENTEROLOGIA (AMBULATÓRIO)',
  bloco: 'BLOCO CIRURGICO',
  enfCirurgia: '9º  SUL',
  ambUro: 'UROLOGIA (AMBULATÓRIO)',
  ambOnco: 'ONCOLOGIA (AMBULATÓRIO)',
  cabecaPescoco: 'CIRURGIA DE CABECA E PESCOCO',
  ambDermato: 'DERMATOLOGIA (AMBULATÓRIO)',
  enfPneumo: '8º NORTE',
  enfClinica: '5º NORTE',
  ambGineco: 'GINECOLOGIA (AMBULATÓRIO)',
  uapHisto: 'UAP: HISTOPATOLÓGICO',
  uapIhq: 'UAP: IMUNOHISTOQUÍMICA',
  uapCcv: 'UAP: CITOLOGIA CÉRVICO-VAGINAL',
  endoscopia: 'ENDOSCOPIA',
};

// ---------------------------------------------------------------------------
// Utilitários de tempo e identificadores
// ---------------------------------------------------------------------------

const HORA = 3_600_000;
const DIA = 24 * HORA;

/**
 * Cria a carga inicial completa relativa ao instante informado.
 */
export function criarCargaInicial(agora: Date): MockDb {
  const now = agora.getTime();
  const iso = (ms: number) => new Date(ms).toISOString();
  const diasAtras = (dias: number) => now - dias * DIA;
  /** Data local AAAA-MM-DD (o AGHU não fornece hora da solicitação). */
  const dataLocal = (ms: number) => {
    const d = new Date(ms);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  };

  const seq = { historico: 0, conferencia: 0, naoConformidade: 0, devolucao: 0, auditoria: 0 };
  const solicitacoes: SolicitacaoAghu[] = [];
  const casos: CasoAp[] = [];
  const conferencias: ConferenciaRecebimento[] = [];
  const naoConformidades: NaoConformidade[] = [];
  const devolucoes: Devolucao[] = [];

  interface SolicitacaoParams {
    codigo: string;
    paciente: PacienteFicticio;
    tipo: TipoExame;
    /** Sigla do exame no AGHU (padrão: a sigla mais comum do tipo). */
    sigla?: string;
    /** Descrição do material da amostra única (atalho para `amostras`). */
    material?: string;
    /** Amostras do exame: [número, descrição, código de status do item]. */
    amostras?: [string, string, string][];
    info: string;
    origem: OrigemAtendimento;
    unidade: string;
    medico: { especialidade: string };
    solicitadaHa: number;
    prontuario?: string;
    /** Status do item quando o exame tem amostra única (padrão: CO, coletado). */
    status?: string;
  }

  /** Amostra do AGHU com a descrição oficial do status. */
  const amostra = (numero: string, descricao: string, status: string, sigla: string): AmostraAghu => ({
    numeroAmostra: numero,
    siglaExame: sigla,
    nomeExame: EXAMES_AGHU[sigla]?.nome ?? sigla,
    descricaoMaterial: descricao,
    codStatusItem: status,
    statusItemDescricao: ({ LI: 'LIBERADO', AC: 'A COLETAR', EX: 'EXECUTANDO', AE: 'AREA EXECUTORA', CA: 'CANCELADO', CO: 'COLETADO', EC: 'EM COLETA', PE: 'PENDENTE' } as Record<string, string>)[status] ?? status,
  });

  /** Monta o grupo de um tipo de exame de uma solicitação AGHU fictícia. */
  const solicitacao = (p: SolicitacaoParams): SolicitacaoAghu => {
    const sigla = p.sigla ?? SIGLA_PADRAO[p.tipo];
    const externo = p.origem === 'EXTERNO';
    return resumirExamesDoGrupo({
      id: chaveExame(p.codigo, p.tipo),
      codigoSolicitacao: p.codigo,
      prontuario: externo ? '' : (p.prontuario ?? p.paciente.prontuario),
      nomePaciente: p.paciente.nome,
      dataNascimento: p.paciente.nascimento,
      origem: p.origem,
      unidade: p.unidade,
      especialidade: externo ? '' : p.medico.especialidade,
      dataSolicitacao: dataLocal(diasAtras(p.solicitadaHa)),
      siglaExame: '',
      nomeExame: '',
      tipoExameSugerido: p.tipo,
      informacoesClinicas: p.info,
      amostras: (p.amostras ?? [['1', p.material ?? '', p.status ?? 'CO']]).map(([n, d, st]) => amostra(n, d, st, sigla)),
      situacaoRecepcao: 'AGUARDANDO_RECEBIMENTO',
    });
  };

  const evento = (
    ocorridoEm: number,
    usuario: Responsavel,
    setor: string,
    eventoCodigo: string,
    titulo: string,
    descricao?: string,
  ): HistoricoCaso => ({
    id: ++seq.historico,
    evento: eventoCodigo,
    titulo,
    descricao,
    setor,
    usuario,
    ocorridoEm: iso(ocorridoEm),
  });

  /** Responsável padrão de cada etapa. */
  const responsavelEtapa = (etapa: EtapaCodigo, tipo: TipoCasoPrincipal): Responsavel => {
    switch (etapa) {
      case 'RECEPCAO':
        return EQUIPE.recepcao;
      case 'MACROSCOPIA':
        return EQUIPE.macroscopia;
      case 'CONGELACAO':
        return EQUIPE.patologista2;
      case 'PROCESSAMENTO':
        return EQUIPE.processamento;
      case 'IHQ':
        return EQUIPE.ihq;
      case 'TRIAGEM_CITO':
        return EQUIPE.citotecnico;
      case 'MICROSCOPIA':
        return tipo === 'CCV' ? EQUIPE.residente2 : EQUIPE.residente;
      case 'APROVACAO':
        return EQUIPE.patologista;
      default:
        return EQUIPE.arquivo;
    }
  };

  /** Registro somente leitura de uma etapa concluída (dados fictícios). */
  const registroEtapa = (
    etapa: EtapaCodigo,
    tipo: TipoCasoPrincipal,
    material: string,
    blocos: number,
    quando: number,
  ): RegistroEtapa | null => {
    const responsavel = responsavelEtapa(etapa, tipo);
    const base = { etapa, responsavel, registradoEm: iso(quando) };
    switch (etapa) {
      case 'MACROSCOPIA':
        return {
          ...base,
          titulo: 'Descrição macroscópica',
          campos: [
            { rotulo: 'Tipo de material', valor: material },
            { rotulo: 'Fragmentos', valor: String(blocos + 1) },
            { rotulo: 'Cassetes', valor: String(blocos) },
            { rotulo: 'Sobra em fixador', valor: blocos > 1 ? 'Sim' : 'Não' },
            { rotulo: 'Rota de processamento', valor: 'Histotécnico' },
          ],
          texto: `Recebido em frasco com formol a 10% material identificado como "${material}". Mede em conjunto 2,1 x 1,4 x 0,7 cm, superfície pardacenta e consistência elástica. Material incluído em ${blocos} cassete(s).`,
        };
      case 'CONGELACAO':
        return {
          ...base,
          titulo: 'Exame intraoperatório (congelação)',
          campos: [
            { rotulo: 'Patologista de plantão', valor: EQUIPE.patologista2.nome },
            { rotulo: 'Lâminas no criostato', valor: '2' },
            { rotulo: 'Resultado comunicado à sala às', valor: new Date(quando).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) },
          ],
          texto: 'Diagnóstico intraoperatório: lesão representada no material examinado. Conclusão definitiva após processamento em parafina.',
        };
      case 'PROCESSAMENTO':
        if (tipo === 'HP') {
          return {
            ...base,
            titulo: 'Processamento técnico',
            campos: [
              { rotulo: 'Rota', valor: 'Histotécnico' },
              { rotulo: 'Blocos', valor: String(blocos) },
              { rotulo: 'Lâminas', valor: String(blocos) },
              { rotulo: 'Coloração', valor: 'Hematoxilina-eosina (HE)' },
            ],
          };
        }
        if (tipo === 'CG') {
          return {
            ...base,
            titulo: 'Processamento citológico',
            campos: [
              { rotulo: 'Rota', valor: 'Citologia direta' },
              { rotulo: 'Material líquido', valor: 'Sim' },
              { rotulo: 'Centrifugado', valor: 'Sim' },
              { rotulo: 'Cell-block', valor: 'Sim' },
              { rotulo: 'Coloração', valor: 'Papanicolaou' },
            ],
          };
        }
        return {
          ...base,
          titulo: 'Processamento citológico',
          campos: [
            { rotulo: 'Rota', valor: 'Citologia direta' },
            { rotulo: 'Lâminas', valor: '1' },
            { rotulo: 'Coloração', valor: 'Papanicolaou' },
          ],
        };
      case 'TRIAGEM_CITO':
        return {
          ...base,
          titulo: 'Triagem citotécnica',
          campos: [
            { rotulo: 'Adequabilidade', valor: 'Satisfatória' },
            { rotulo: 'Resultado da triagem', valor: 'Sem alterações citológicas significativas' },
          ],
        };
      case 'MICROSCOPIA':
        return {
          ...base,
          titulo: 'Parecer preliminar',
          campos: [{ rotulo: 'Residente', valor: responsavel.nome }],
          texto: 'Cortes histológicos/esfregaços examinados. Achados descritos para revisão e validação pela preceptoria.',
        };
      case 'APROVACAO':
        return {
          ...base,
          titulo: 'Laudo',
          campos: [
            { rotulo: 'Patologista responsável', valor: EQUIPE.patologista.nome },
            { rotulo: 'Residente', valor: tipo === 'CCV' ? EQUIPE.residente2.nome : EQUIPE.residente.nome },
          ],
          texto: 'Conclusão diagnóstica registrada (texto fictício para demonstração). Laudo liberado no AGHU pela rotina institucional.',
        };
      case 'ARQUIVO':
        return {
          ...base,
          titulo: 'Arquivamento',
          campos: [
            { rotulo: 'Local', valor: 'Arquivo de blocos e lâminas – Armário 3, gaveta 12' },
            { rotulo: 'Ficha arquivada', valor: 'Sim' },
            { rotulo: 'Cadastro no Siscan', valor: tipo === 'CCV' ? 'Realizado' : 'Não se aplica' },
          ],
        };
      default:
        return null;
    }
  };

  interface CasoParams {
    numero: string;
    tipo: TipoCasoPrincipal;
    sol: SolicitacaoAghu;
    status: StatusCaso;
    /** Etapa atual; `null` quando arquivado. */
    etapaAtual: EtapaCodigo | null;
    entradaHa: number;
    procedimento: string;
    urgente?: boolean;
    blocos?: number;
    ihqs?: Omit<ExameIhq, 'registradaPor' | 'recebidaEm'>[];
    observacoes?: string;
  }

  /** Cria um caso coerente com seu status: etapas, registros, materiais e histórico. */
  const caso = (p: CasoParams): CasoAp => {
    const t0 = diasAtras(p.entradaHa);
    const quantidade = p.sol.amostras.length;
    const blocos = p.blocos ?? 2;
    const possuiIhq = (p.ihqs?.length ?? 0) > 0;
    const fluxo = fluxoDoCaso(p.tipo, possuiIhq);
    const indiceAtual = p.etapaAtual === null ? fluxo.length : fluxo.indexOf(p.etapaAtual);
    const aguardandoChegada = p.status === 'RECEBIDO' || p.status === 'LAUDO_CONCLUIDO';
    const slot = (now - t0) / Math.max(indiceAtual + 0.5, 1);

    const etapas: CasoEtapa[] = [];
    const registros: RegistroEtapa[] = [];
    const historico: HistoricoCaso[] = [];
    const setorRecepcao = ETAPAS.RECEPCAO;

    // Recepção
    etapas.push({
      etapa: 'RECEPCAO',
      sequencia: 1,
      status: 'CONCLUIDA',
      iniciadaEm: iso(t0),
      concluidaEm: iso(t0),
      responsavelInicio: EQUIPE.recepcao,
      responsavelFim: EQUIPE.recepcao,
    });
    historico.push(
      evento(
        t0,
        EQUIPE.recepcao,
        setorRecepcao,
        'ENTRADA_CONFIRMADA',
        'Entrada confirmada',
        `Nº interno ${p.numero} gerado a partir da solicitação AGHU ${p.sol.codigoSolicitacao}. Conferência aceita.`,
      ),
    );
    if (p.urgente) {
      historico.push(evento(t0, EQUIPE.recepcao, setorRecepcao, 'URGENCIA_MARCADA', 'Marcado como URGENTE', 'Urgência da solicitação AGHU.'));
    }

    // Etapas posteriores
    let etapaAtualDesde = t0;
    for (let i = 1; i < fluxo.length; i++) {
      const etapa = fluxo[i];
      const responsavel = responsavelEtapa(etapa, p.tipo);
      const inicio = t0 + slot * (i - 1) + slot * 0.15;
      const fim = t0 + slot * i;
      if (i < indiceAtual) {
        etapas.push({
          etapa,
          sequencia: i + 1,
          status: 'CONCLUIDA',
          iniciadaEm: iso(inicio),
          concluidaEm: iso(fim),
          responsavelInicio: responsavel,
          responsavelFim: responsavel,
        });
        historico.push(evento(inicio, responsavel, ETAPAS[etapa], 'ETAPA_RECEBIDA', `Chegada registrada em ${ETAPAS[etapa]}`));
        historico.push(evento(fim, responsavel, ETAPAS[etapa], 'ETAPA_CONCLUIDA', `${ETAPAS[etapa]} concluída`));
        const registro = registroEtapa(etapa, p.tipo, resumoMaterial(p.sol), blocos, fim);
        if (registro) registros.push(registro);
      } else if (i === indiceAtual) {
        if (aguardandoChegada) {
          etapas.push({ etapa, sequencia: i + 1, status: 'PENDENTE' });
          etapaAtualDesde = i === 1 ? t0 : t0 + slot * (i - 1);
        } else {
          etapas.push({
            etapa,
            sequencia: i + 1,
            status: 'EM_ANDAMENTO',
            iniciadaEm: iso(inicio),
            responsavelInicio: responsavel,
          });
          historico.push(evento(inicio, responsavel, ETAPAS[etapa], 'ETAPA_RECEBIDA', `Chegada registrada em ${ETAPAS[etapa]}`));
          etapaAtualDesde = inicio;
        }
      }
    }
    if (p.etapaAtual === null) etapaAtualDesde = t0 + slot * (fluxo.length - 1);

    const concluida = (etapa: EtapaCodigo) => fluxo.indexOf(etapa) > -1 && fluxo.indexOf(etapa) < indiceAtual;
    const quandoConcluida = (etapa: EtapaCodigo) => iso(t0 + slot * fluxo.indexOf(etapa));
    const statusItem = p.status === 'ARQUIVADO' ? 'ARQUIVADO' : 'DISPONIVEL';

    // Materiais: amostras-raiz e derivados conforme as etapas concluídas
    const materiais: ItemMaterial[] = [];
    for (let a = 1; a <= quantidade; a++) {
      const amostraAghu = p.sol.amostras[a - 1];
      const codigoAmostra = a === 1 ? p.numero : `${p.numero}-F${a}`;
      const amostra: ItemMaterial = {
        codigo: codigoAmostra,
        tipoItem: 'AMOSTRA',
        rotulo: `Amostra ${amostraAghu.numeroAmostra}`,
        descricao: amostraAghu.descricaoMaterial,
        numeroAmostraAghu: amostraAghu.numeroAmostra,
        origem: 'ROTINA',
        status: statusItem,
        criadoPor: EQUIPE.recepcao,
        criadoEm: iso(t0),
        filhos: [],
      };
      if (p.tipo === 'HP' && concluida('MACROSCOPIA')) {
        for (let b = 0; b < blocos; b++) {
          const letra = String.fromCharCode(65 + b);
          const bloco: ItemMaterial = {
            codigo: `${codigoAmostra}-${letra}`,
            tipoItem: 'BLOCO',
            rotulo: `Bloco ${letra}`,
            origem: 'ROTINA',
            status: statusItem,
            criadoPor: EQUIPE.macroscopia,
            criadoEm: quandoConcluida('MACROSCOPIA'),
            filhos: [],
          };
          if (concluida('PROCESSAMENTO')) {
            bloco.filhos.push({
              codigo: `${bloco.codigo}-01`,
              tipoItem: 'LAMINA',
              rotulo: `Lâmina ${letra}-01 · HE`,
              origem: 'ROTINA',
              status: statusItem,
              criadoPor: EQUIPE.processamento,
              criadoEm: quandoConcluida('PROCESSAMENTO'),
              filhos: [],
            });
          }
          amostra.filhos.push(bloco);
        }
      }
      if (p.tipo === 'CO' && concluida('CONGELACAO')) {
        amostra.filhos.push({
          codigo: `${codigoAmostra}-C`,
          tipoItem: 'BLOCO',
          rotulo: 'Bloco de congelação',
          origem: 'CONGELACAO',
          status: statusItem,
          criadoPor: EQUIPE.patologista2,
          criadoEm: quandoConcluida('CONGELACAO'),
          filhos: [
            {
              codigo: `${codigoAmostra}-C-01`,
              tipoItem: 'LAMINA',
              rotulo: 'Lâmina C-01 · criostato',
              origem: 'CONGELACAO',
              status: statusItem,
              criadoPor: EQUIPE.patologista2,
              criadoEm: quandoConcluida('CONGELACAO'),
              filhos: [],
            },
          ],
        });
      }
      if ((p.tipo === 'CG' || p.tipo === 'CCV') && concluida('PROCESSAMENTO')) {
        if (p.tipo === 'CG') {
          amostra.filhos.push({
            codigo: `${codigoAmostra}-CB`,
            tipoItem: 'CELL_BLOCK',
            rotulo: 'Cell-block',
            origem: 'ROTINA',
            status: statusItem,
            criadoPor: EQUIPE.processamento,
            criadoEm: quandoConcluida('PROCESSAMENTO'),
            filhos: [],
          });
        }
        amostra.filhos.push({
          codigo: `${codigoAmostra}-L01`,
          tipoItem: 'LAMINA',
          rotulo: 'Lâmina direta 01 · Papanicolaou',
          origem: 'ROTINA',
          status: statusItem,
          criadoPor: EQUIPE.processamento,
          criadoEm: quandoConcluida('PROCESSAMENTO'),
          filhos: [],
        });
      }
      materiais.push(amostra);
    }

    // IHQ vinculadas
    const ihqs: ExameIhq[] = (p.ihqs ?? []).map((ihq) => {
      const recebida = t0 + slot * Math.max(fluxo.indexOf('IHQ') - 1, 1);
      historico.push(
        evento(
          recebida,
          EQUIPE.recepcao,
          setorRecepcao,
          'IHQ_VINCULADA',
          `IHQ ${ihq.codigoInternoIhq} vinculada ao caso`,
          `Solicitação AGHU ${ihq.solicitacaoAghuCodigo} recebida pela recepção.`,
        ),
      );
      if (ihq.status === 'AGUARDANDO_EXTERNO') {
        historico.push(
          evento(
            recebida + 2 * HORA,
            EQUIPE.ihq,
            ETAPAS.IHQ,
            'IHQ_ENVIADA_EXTERNO',
            `IHQ ${ihq.codigoInternoIhq} enviada ao laboratório externo`,
            ihq.laboratorioExterno,
          ),
        );
      }
      return { ...ihq, recebidaEm: iso(recebida), registradaPor: EQUIPE.recepcao };
    });

    // Situação da solicitação AGHU
    const sol: SolicitacaoAghu = { ...p.sol, situacaoRecepcao: 'RECEBIDA', casoNumero: p.numero };
    solicitacoes.push(sol);

    conferencias.push({
      id: ++seq.conferencia,
      solicitacaoId: sol.id,
      solicitacaoCodigo: sol.codigoSolicitacao,
      casoNumero: p.numero,
      amostras: sol.amostras.map((a) => a.numeroAmostra),
      resultado: 'ACEITA',
      conferidoPor: EQUIPE.recepcao,
      conferidoEm: iso(t0),
    });

    const novo: CasoAp = {
      numeroInterno: p.numero,
      tipoExame: p.tipo,
      solicitacao: sol,
      status: p.status,
      etapaAtual: p.etapaAtual,
      etapaAtualDesde: iso(etapaAtualDesde),
      dataEntradaSap: iso(t0),
      responsavelEntrada: EQUIPE.recepcao,
      urgente: Boolean(p.urgente),
      procedimento: p.procedimento,
      quantidade,
      observacoes: p.observacoes,
      etapas,
      registros,
      materiais,
      ihqs,
      naoConformidades: [],
      devolucoes: [],
      historico,
    };
    casos.push(novo);
    return novo;
  };

  // -------------------------------------------------------------------------
  // Casos (todos os 13 status)
  // -------------------------------------------------------------------------

  caso({
    numero: 'HP-0001/26', tipo: 'HP', status: 'ARQUIVADO', etapaAtual: null, entradaHa: 58, procedimento: 'Biópsia endoscópica', blocos: 1,
    sol: solicitacao({ codigo: '7710214', paciente: P.odete, tipo: 'HP', material: 'BIÓPSIA GÁSTRICA – ANTRO', info: 'Dispepsia persistente. Endoscopia com área de enantema em antro. Pesquisa de H. pylori.', origem: 'AMBULATORIO', unidade: U.ambGastro, medico: MED.gastro, solicitadaHa: 59 }),
  });
  caso({
    numero: 'HP-0002/26', tipo: 'HP', status: 'EM_ARQUIVAMENTO', etapaAtual: 'ARQUIVO', entradaHa: 41, procedimento: 'Ressecção cirúrgica',
    sol: solicitacao({ codigo: '7710388', paciente: P.gerson, tipo: 'HP', material: 'VESÍCULA BILIAR', info: 'Colelitíase sintomática. Colecistectomia videolaparoscópica eletiva.', origem: 'CIRURGIA', unidade: U.bloco, medico: MED.cirurgia, solicitadaHa: 41 }),
  });
  caso({
    numero: 'HP-0003/26', tipo: 'HP', status: 'LAUDO_CONCLUIDO', etapaAtual: 'ARQUIVO', entradaHa: 30, procedimento: 'Histerectomia', blocos: 4,
    sol: solicitacao({ codigo: '7710457', paciente: P.iracema, tipo: 'HP', material: 'ÚTERO E ANEXOS', info: 'Miomatose uterina com sangramento uterino anormal. Histerectomia total.', origem: 'INTERNACAO', unidade: U.enfCirurgia, medico: MED.gineco, solicitadaHa: 31 }),
  });
  caso({
    numero: 'HP-0004/26', tipo: 'HP', status: 'AGUARDANDO_APROVACAO', etapaAtual: 'APROVACAO', entradaHa: 16, procedimento: 'Biópsia por agulha grossa',
    urgente: true,
    sol: solicitacao({ codigo: '7710593', paciente: P.wilson, tipo: 'HP', amostras: [['1', 'PRÓSTATA LOBO DIREITO – 6 FRAGMENTOS', 'EX'], ['2', 'PRÓSTATA LOBO ESQUERDO – 6 FRAGMENTOS', 'EX']], info: 'PSA elevado em controle. Toque retal com nódulo em lobo direito.', origem: 'AMBULATORIO', unidade: U.ambUro, medico: MED.uro, solicitadaHa: 17 }),
  });
  caso({
    numero: 'HP-0005/26', tipo: 'HP', status: 'EM_MICROSCOPIA', etapaAtual: 'MICROSCOPIA', entradaHa: 20, procedimento: 'Biópsia endoscópica',
    ihqs: [{ codigoInternoIhq: 'IH-0001/26', status: 'RESULTADO_REGISTRADO', solicitacaoAghuCodigo: '7710980', anticorpos: ['CK7', 'CK20', 'CDX2'], resultadoTecnico: 'Reações realizadas internamente; controles adequados.' }],
    sol: solicitacao({ codigo: '7710642', paciente: P.neide, tipo: 'HP', material: 'BIÓPSIA DE CÓLON – SIGMOIDE', info: 'Alteração do hábito intestinal. Colonoscopia com lesão vegetante em sigmoide.', origem: 'AMBULATORIO', unidade: U.ambGastro, medico: MED.gastro, solicitadaHa: 21 }),
  });
  caso({
    numero: 'HP-0006/26', tipo: 'HP', status: 'IHQ_AGUARDANDO_EXTERNO', etapaAtual: 'IHQ', entradaHa: 18, procedimento: 'Biópsia por agulha grossa',
    ihqs: [{ codigoInternoIhq: 'IH-0002/26', status: 'AGUARDANDO_EXTERNO', solicitacaoAghuCodigo: '7711010', anticorpos: ['HER2'], laboratorioExterno: 'Laboratório de Referência em Patologia (fictício)' }],
    sol: solicitacao({ codigo: '7710731', paciente: P.telma, tipo: 'HP', material: 'NÓDULO DE MAMA ESQUERDA – CORE BIOPSY', info: 'Nódulo palpável em quadrante superior externo da mama esquerda, BI-RADS 4.', origem: 'AMBULATORIO', unidade: U.ambOnco, medico: MED.mastologia, solicitadaHa: 18 }),
  });
  caso({
    numero: 'HP-0007/26', tipo: 'HP', status: 'EM_IHQ', etapaAtual: 'IHQ', entradaHa: 12, procedimento: 'Biópsia excisional',
    ihqs: [{ codigoInternoIhq: 'IH-0003/26', status: 'EM_EXECUCAO_INTERNA', solicitacaoAghuCodigo: '7711236', anticorpos: ['CD20', 'CD3', 'Ki-67'] }],
    sol: solicitacao({ codigo: '7710866', paciente: P.ednaldo, tipo: 'HP', material: 'LINFONODO CERVICAL', info: 'Linfonodomegalia cervical persistente há 3 meses, sem febre.', origem: 'AMBULATORIO', unidade: U.cabecaPescoco, medico: MED.cabecaPescoco, solicitadaHa: 13 }),
  });
  caso({
    numero: 'HP-0008/26', tipo: 'HP', status: 'EM_PROCESSAMENTO', etapaAtual: 'PROCESSAMENTO', entradaHa: 6, procedimento: 'Ressecção cirúrgica', blocos: 1,
    sol: solicitacao({ codigo: '7711024', paciente: P.zuleide, tipo: 'HP', material: 'APÊNDICE CECAL', info: 'Quadro de abdome agudo. Apendicectomia de urgência.', origem: 'CIRURGIA', unidade: U.bloco, medico: MED.cirurgia, solicitadaHa: 6 }),
  });
  caso({
    numero: 'HP-0009/26', tipo: 'HP', status: 'EM_MACROSCOPIA', etapaAtual: 'MACROSCOPIA', entradaHa: 2, procedimento: 'Biópsia endoscópica',
    urgente: true,
    sol: solicitacao({ codigo: '7711267', paciente: P.valter, tipo: 'HP', material: 'BIÓPSIA GÁSTRICA – CORPO', info: 'Emagrecimento e lesão ulcerada em corpo gástrico à endoscopia.', origem: 'AMBULATORIO', unidade: U.ambGastro, medico: MED.gastro, solicitadaHa: 2 }),
  });
  caso({
    numero: 'HP-0010/26', tipo: 'HP', status: 'RECEBIDO', etapaAtual: 'MACROSCOPIA', entradaHa: 0.3, procedimento: 'Exérese de lesão cutânea',
    sol: solicitacao({ codigo: '7711390', paciente: P.mirtes, tipo: 'HP', sigla: 'HPDER', material: 'LESÃO DE PELE – DORSO', info: 'Lesão pigmentada assimétrica em dorso, 0,8 cm. Exérese com margem.', origem: 'AMBULATORIO', unidade: U.ambDermato, medico: MED.dermato, solicitadaHa: 1 }),
  });
  const casoDevolvido = caso({
    numero: 'HP-0011/26', tipo: 'HP', status: 'DEVOLVIDO', etapaAtual: 'MACROSCOPIA', entradaHa: 9, procedimento: 'Ressecção cirúrgica',
    sol: solicitacao({ codigo: '7711455', paciente: P.jurandir, tipo: 'HP', material: 'SEGMENTO DE INTESTINO DELGADO', info: 'Obstrução intestinal. Enterectomia segmentar.', origem: 'CIRURGIA', unidade: U.bloco, medico: MED.cirurgia, solicitadaHa: 9 }),
  });
  caso({
    numero: 'CG-0001/26', tipo: 'CG', status: 'EM_MICROSCOPIA', etapaAtual: 'MICROSCOPIA', entradaHa: 10, procedimento: 'Coleta de líquido cavitário',
    sol: solicitacao({ codigo: '7710912', paciente: P.cleonice, tipo: 'CG', material: 'LÍQUIDO PLEURAL', info: 'Derrame pleural à direita de etiologia a esclarecer.', origem: 'INTERNACAO', unidade: U.enfPneumo, medico: MED.clinica, solicitadaHa: 10 }),
  });
  caso({
    numero: 'CG-0002/26', tipo: 'CG', status: 'EM_PROCESSAMENTO', etapaAtual: 'PROCESSAMENTO', entradaHa: 1, procedimento: 'Coleta de líquido cavitário',
    urgente: true,
    sol: solicitacao({ codigo: '7711302', paciente: P.ademir, tipo: 'CG', material: 'LÍQUIDO ASCÍTICO', info: 'Ascite volumosa de início recente. Paracentese diagnóstica.', origem: 'INTERNACAO', unidade: U.enfClinica, medico: MED.clinica, solicitadaHa: 1 }),
  });
  const casoCancelado = caso({
    numero: 'CG-0003/26', tipo: 'CG', status: 'CANCELADO', etapaAtual: 'PROCESSAMENTO', entradaHa: 7, procedimento: 'Punção aspirativa por agulha fina (PAAF)',
    sol: solicitacao({ codigo: '7711088', paciente: P.socorro, tipo: 'CG', material: 'PAAF DE TIREOIDE', info: 'Nódulo tireoidiano TI-RADS 4 em lobo esquerdo.', origem: 'AMBULATORIO', unidade: U.cabecaPescoco, medico: MED.cabecaPescoco, solicitadaHa: 8 }),
  });
  caso({
    numero: 'CCV-0001/26', tipo: 'CCV', status: 'AGUARDANDO_APROVACAO', etapaAtual: 'APROVACAO', entradaHa: 14, procedimento: 'Coleta de citologia cérvico-vaginal',
    sol: solicitacao({ codigo: '7710805', paciente: P.rosimere, tipo: 'CCV', material: 'ESFREGAÇO CÉRVICO-VAGINAL', info: 'Rastreamento de rotina. Última coleta há 3 anos.', origem: 'AMBULATORIO', unidade: U.ambGineco, medico: MED.gineco, solicitadaHa: 15 }),
  });
  caso({
    numero: 'CCV-0002/26', tipo: 'CCV', status: 'EM_PROCESSAMENTO', etapaAtual: 'PROCESSAMENTO', entradaHa: 3, procedimento: 'Coleta de citologia cérvico-vaginal',
    sol: solicitacao({ codigo: '7711199', paciente: P.marinalva, tipo: 'CCV', material: 'ESFREGAÇO CÉRVICO-VAGINAL', info: 'Controle após tratamento de lesão de baixo grau.', origem: 'AMBULATORIO', unidade: U.ambGineco, medico: MED.gineco, solicitadaHa: 3 }),
  });
  caso({
    numero: 'CCV-0003/26', tipo: 'CCV', status: 'ARQUIVADO', etapaAtual: null, entradaHa: 50, procedimento: 'Coleta de citologia cérvico-vaginal',
    sol: solicitacao({ codigo: '7710301', paciente: P.doralice, tipo: 'CCV', material: 'ESFREGAÇO CÉRVICO-VAGINAL', info: 'Rastreamento de rotina.', origem: 'EXTERNO', unidade: U.uapCcv, medico: MED.externo, solicitadaHa: 51 }),
  });
  caso({
    numero: 'CO-0001/26', tipo: 'CO', status: 'EM_CONGELACAO', etapaAtual: 'CONGELACAO', entradaHa: 35 / (24 * 60), procedimento: 'Biópsia intraoperatória',
    urgente: true,
    sol: solicitacao({ codigo: '7711501', paciente: P.gloria, tipo: 'CO', material: 'NÓDULO DE TIREOIDE – PEÇA INTRAOPERATÓRIA', info: 'Tireoidectomia parcial. Avaliar malignidade para decisão de totalização.', origem: 'CIRURGIA', unidade: U.bloco, medico: MED.cabecaPescoco, solicitadaHa: 0.05 }),
  });
  caso({
    numero: 'CO-0002/26', tipo: 'CO', status: 'EM_MICROSCOPIA', etapaAtual: 'MICROSCOPIA', entradaHa: 4, procedimento: 'Biópsia intraoperatória',
    sol: solicitacao({ codigo: '7711143', paciente: P.leonardo, tipo: 'CO', material: 'NÓDULO PULMONAR – CONGELAÇÃO', info: 'Nódulo pulmonar periférico de 1,9 cm. Ressecção em cunha.', origem: 'CIRURGIA', unidade: U.bloco, medico: MED.toracica, solicitadaHa: 4 }),
  });

  // Solicitações AGHU das IHQ já vinculadas
  const solsIhq: [string, PacienteFicticio, string, { especialidade: string }, number, string][] = [
    ['7710980', P.neide, 'BLOCO A – HP-0005/26', MED.gastro, 15, 'IH-0001/26|HP-0005/26'],
    ['7711010', P.telma, 'BLOCO A – HP-0006/26', MED.mastologia, 12, 'IH-0002/26|HP-0006/26'],
    ['7711236', P.ednaldo, 'BLOCO B – HP-0007/26', MED.cabecaPescoco, 5, 'IH-0003/26|HP-0007/26'],
  ];
  for (const [codigo, paciente, material, medico, ha, vinculo] of solsIhq) {
    const [ihqCodigo, casoNumero] = vinculo.split('|');
    solicitacoes.push({
      ...solicitacao({ codigo, paciente, tipo: 'IHQ', material, info: 'Painel imuno-histoquímico solicitado pela microscopia.', origem: 'AMBULATORIO', unidade: U.uapIhq, medico, solicitadaHa: ha, status: 'EX' }),
      situacaoRecepcao: 'RECEBIDA',
      ihqCodigo,
      ihqCasoNumero: casoNumero,
    });
  }

  // -------------------------------------------------------------------------
  // Devolução de caso (HP-0011/26) e cancelamento (CG-0003/26)
  // -------------------------------------------------------------------------

  const devolvidoEm = diasAtras(9) + 20 * HORA;
  naoConformidades.push({
    id: ++seq.naoConformidade,
    casoNumero: casoDevolvido.numeroInterno,
    solicitacaoCodigo: casoDevolvido.solicitacao.codigoSolicitacao,
    tipo: 'ACONDICIONAMENTO_INADEQUADO',
    descricao: '',
    observacao: 'Peça recebida sem formol no recipiente, com sinais de ressecamento.',
    setor: ETAPAS.MACROSCOPIA,
    etapa: ETAPAS.MACROSCOPIA,
    etapaCodigo: 'MACROSCOPIA',
    unidadeOrigem: casoDevolvido.solicitacao.unidade,
    registradoPor: EQUIPE.macroscopia,
    registradoEm: iso(devolvidoEm),
    status: 'ABERTA',
  });
  devolucoes.push({
    id: ++seq.devolucao,
    naoConformidadeId: seq.naoConformidade,
    casoNumero: casoDevolvido.numeroInterno,
    solicitacaoCodigo: casoDevolvido.solicitacao.codigoSolicitacao,
    unidadeOrigem: casoDevolvido.solicitacao.unidade,
    devolvidoPor: EQUIPE.macroscopia,
    novaAmostraSolicitada: true,
    situacao: 'AGUARDANDO_NOVA_AMOSTRA',
    devolvidaEm: iso(devolvidoEm),
  });
  casoDevolvido.historico.push(
    evento(devolvidoEm, EQUIPE.macroscopia, ETAPAS.MACROSCOPIA, 'NAO_CONFORMIDADE', 'Não conformidade registrada', 'Acondicionamento inadequado ou sem fixador. — Peça recebida sem formol no recipiente.'),
    evento(devolvidoEm, EQUIPE.macroscopia, ETAPAS.MACROSCOPIA, 'DEVOLUCAO', 'Material devolvido à origem', 'Devolvido à unidade de origem. Nova amostra solicitada: Sim.'),
  );

  const canceladoEm = diasAtras(6);
  casoCancelado.cancelamento = {
    motivo: 'Solicitação duplicada no AGHU: o mesmo material foi registrado em outra solicitação.',
    canceladoPor: EQUIPE.chefia,
    canceladoEm: iso(canceladoEm),
  };
  casoCancelado.historico.push(
    evento(canceladoEm, EQUIPE.chefia, 'Chefia', 'CASO_CANCELADO', 'Caso cancelado', casoCancelado.cancelamento.motivo),
  );

  // -------------------------------------------------------------------------
  // Rejeições na recepção (sem caso)
  // -------------------------------------------------------------------------

  const rejeitadaEm = diasAtras(4);
  const solRejeitada: SolicitacaoAghu = {
    ...solicitacao({ codigo: '7712045', paciente: P.gilvan, tipo: 'HP', material: 'BIÓPSIA DE PELE – ANTEBRAÇO', info: 'Lesão eritematodescamativa em antebraço direito há 6 meses.', origem: 'AMBULATORIO', unidade: U.ambDermato, medico: MED.dermato, solicitadaHa: 5 }),
    situacaoRecepcao: 'DEVOLVIDA',
  };
  conferencias.push({
    id: ++seq.conferencia,
    solicitacaoId: solRejeitada.id,
    solicitacaoCodigo: solRejeitada.codigoSolicitacao,
    amostras: solRejeitada.amostras.map((a) => a.numeroAmostra),
    resultado: 'REJEITADA',
    observacao: 'Outros: Nome no frasco diverge do nome na requisição (sobrenome trocado).',
    conferidoPor: EQUIPE.recepcao2,
    conferidoEm: iso(rejeitadaEm),
  });
  naoConformidades.push({
    id: ++seq.naoConformidade,
    solicitacaoCodigo: solRejeitada.codigoSolicitacao,
    tipo: 'OUTROS',
    descricao: 'Nome no frasco diverge do nome na requisição (sobrenome trocado).',
    setor: ETAPAS.RECEPCAO,
    etapa: 'Recepção (conferência)',
    etapaCodigo: 'RECEPCAO',
    unidadeOrigem: solRejeitada.unidade,
    registradoPor: EQUIPE.recepcao2,
    registradoEm: iso(rejeitadaEm),
    status: 'ABERTA',
  });
  devolucoes.push({
    id: ++seq.devolucao,
    naoConformidadeId: seq.naoConformidade,
    solicitacaoCodigo: solRejeitada.codigoSolicitacao,
    unidadeOrigem: solRejeitada.unidade,
    devolvidoPor: EQUIPE.recepcao2,
    novaAmostraSolicitada: true,
    situacao: 'AGUARDANDO_NOVA_AMOSTRA',
    devolvidaEm: iso(rejeitadaEm),
  });
  solRejeitada.devolucaoId = seq.devolucao;
  solicitacoes.push(solRejeitada);

  const semEtiquetaEm = diasAtras(2);
  naoConformidades.push({
    id: ++seq.naoConformidade,
    tipo: 'SEM_SOLICITACAO_OU_ETIQUETA',
    descricao: '',
    observacao: 'Frasco com fragmento de colo uterino sem etiqueta do AGHU, apenas identificação manuscrita.',
    setor: ETAPAS.RECEPCAO,
    etapa: 'Recepção (leitura)',
    etapaCodigo: 'RECEPCAO',
    unidadeOrigem: U.ambGineco,
    registradoPor: EQUIPE.recepcao,
    registradoEm: iso(semEtiquetaEm),
    status: 'RESOLVIDA',
  });
  devolucoes.push({
    id: ++seq.devolucao,
    naoConformidadeId: seq.naoConformidade,
    unidadeOrigem: U.ambGineco,
    devolvidoPor: EQUIPE.recepcao,
    novaAmostraSolicitada: true,
    situacao: 'NOVA_AMOSTRA_RECEBIDA',
    devolvidaEm: iso(semEtiquetaEm),
  });

  // -------------------------------------------------------------------------
  // Solicitações aguardando recebimento
  // -------------------------------------------------------------------------

  solicitacoes.push(
    // Exame com amostra única
    solicitacao({ codigo: '7712301', paciente: P.aurelio, tipo: 'HP', material: 'BIÓPSIA DE ESÔFAGO DISTAL', info: 'Pirose crônica. Endoscopia com mucosa de aspecto colunar em esôfago distal.', origem: 'AMBULATORIO', unidade: U.endoscopia, medico: MED.gastro, solicitadaHa: 0 }),
    solicitacao({ codigo: '7712318', paciente: P.erivaldo, tipo: 'CG', material: 'LÍQUIDO PERITONEAL', info: 'Ascite em paciente com massa pélvica em investigação.', origem: 'INTERNACAO', unidade: U.enfCirurgia, medico: MED.cirurgia, solicitadaHa: 1 }),
    // Paciente Externo: sem prontuário e sem especialidade
    solicitacao({ codigo: '7712325', paciente: P.jandira, tipo: 'CCV', material: 'COLO UTERINO', info: 'Paciente Externo: COLO UTERINO', origem: 'EXTERNO', unidade: U.uapCcv, medico: MED.externo, solicitadaHa: 2, status: 'AE' }),
    // CITO: descrição do material vazia
    solicitacao({ codigo: '7712333', paciente: P.lucineide, tipo: 'CCV', sigla: 'CITO', material: '', info: 'Rastreamento.', origem: 'AMBULATORIO', unidade: U.ambGineco, medico: MED.gineco, solicitadaHa: 3, status: 'AC' }),
    // Mesma solicitação com Congelação e peça cirúrgica (recebimento parcial)
    solicitacao({ codigo: '7712340', paciente: P.osvaldo, tipo: 'CO', material: 'NÓDULO HEPÁTICO – PEÇA INTRAOPERATÓRIA', info: 'Hepatectomia em andamento. Avaliar margem e natureza da lesão.', origem: 'CIRURGIA', unidade: U.bloco, medico: MED.cirurgia, solicitadaHa: 0 }),
    solicitacao({ codigo: '7712340', paciente: P.osvaldo, tipo: 'HP', amostras: [['2', 'SEGMENTO HEPÁTICO VI', 'CO'], ['3', 'VESÍCULA BILIAR', 'AC']], info: 'Hepatectomia em andamento. Avaliar margem e natureza da lesão.', origem: 'CIRURGIA', unidade: U.bloco, medico: MED.cirurgia, solicitadaHa: 0 }),
    // Três amostras de HP e uma de IHQ na mesma solicitação; nome longo (etiqueta)
    solicitacao({ codigo: '7712390', paciente: P.mariaGracas, tipo: 'HP', sigla: 'MBIOP', amostras: [['1', 'MAMA DIREITA 10H', 'CO'], ['2', 'MAMA DIREITA 2H', 'CO'], ['3', 'LINFONODO AXILAR DIREITO', 'EX']], info: 'Nódulos em mama direita BI-RADS 4. Linfonodo axilar suspeito.', origem: 'AMBULATORIO', unidade: U.ambOnco, medico: MED.mastologia, solicitadaHa: 1 }),
    solicitacao({ codigo: '7712390', paciente: P.mariaGracas, tipo: 'IHQ', amostras: [['4', 'MAMA DIREITA 10H – PAINEL RECEPTORES HORMONAIS', 'AE']], info: 'Nódulos em mama direita BI-RADS 4. Linfonodo axilar suspeito.', origem: 'AMBULATORIO', unidade: U.ambOnco, medico: MED.mastologia, solicitadaHa: 1 }),
    // IHQ da mesma solicitação do caso HP-0010/26 (sugestão do caso de origem)
    solicitacao({ codigo: '7711390', paciente: P.mirtes, tipo: 'IHQ', amostras: [['2', 'LESÃO DE PELE – DORSO (BLOCO A)', 'AE']], info: 'Lesão pigmentada assimétrica em dorso, 0,8 cm. Exérese com margem.', origem: 'AMBULATORIO', unidade: U.ambDermato, medico: MED.dermato, solicitadaHa: 1 }),
    solicitacao({ codigo: '7712356', paciente: P.neide, tipo: 'IHQ', material: 'BLOCO A – HP-0005/26 (AMPLIAÇÃO DE PAINEL)', info: 'Ampliação do painel imuno-histoquímico solicitada pela microscopia.', origem: 'AMBULATORIO', unidade: U.uapIhq, medico: MED.gastro, solicitadaHa: 0 }),
    solicitacao({ codigo: '7712372', paciente: P.ednaldo, prontuario: '2276645', tipo: 'IHQ', material: 'BLOCO B – LINFONODO CERVICAL (PAINEL COMPLEMENTAR)', info: 'Painel complementar para linfoma solicitado pela microscopia.', origem: 'AMBULATORIO', unidade: U.uapIhq, medico: MED.cabecaPescoco, solicitadaHa: 0 }),
  );

  return {
    solicitacoes,
    casos,
    conferencias,
    naoConformidades,
    devolucoes,
    auditoria: [],
    aghuDisponivel: true,
    sequencias: seq,
  };
}
