import React from 'react';
import {Composition} from 'remotion';
import {Reel, reelSchemaDefaults} from './Reel';
import {Demo, demoDefaults} from './Demo';
import {Cover, coverDefaults} from './Cover';
import {Twelve, TWELVE_FRAMES} from './Twelve';
import {Showcase, showDefaults, showDuration} from './Showcase';
import {SkillReel, skillDefaults, skillDuration} from './SkillReel';
const SHOTS = [
  {src:'63ee_535-590.mp4',from:15,dur:2.8,title:'Этот сайт — 5 минут',sub:'без дизайнера и программиста',zoom:[1.05,1.15],focus:[0.5,0.45]},
  {src:'3e97_1000-1035.mp4',from:15,dur:2.5,mode:'full',focus:[0.8,0.95],zoom:[1.15,1.22],title:'Этот — одной фразой'},
  {src:'ffd3_490-530.mp4',from:7.5,dur:2.8,focus:[0.66,0.4],zoom:[1.2,1.3],title:'Лендинг под событие',sub:'под каждое мероприятие — за пару минут'},
  {src:'334e_310-330.mp4',from:8,dur:1.8,tag:'БЫЛО',focus:[0.73,0.3],zoom:[1.9,2.0],title:'Обычный сайт'},
  {src:'3e97_1000-1035.mp4',from:20,dur:2.8,tag:'СТАЛО',focus:[0.5,0.5],zoom:[1.0,1.08],title:'После скила дизайна'},
  {src:'3e97_0-20.mp4',from:12.5,dur:2.8,focus:[0.55,0.5],zoom:[1.02,1.12],title:'Робот ходит по сайту',sub:'Claude сделал это сам'},
  {src:'334e_535-605.mp4',from:8,dur:2.8,focus:[0.3,0.3],zoom:[1.9,2.05],title:'Секрет — скил дизайна',sub:'ставится один раз — и Claude рисует как дизайнер'},
];
const COURSES = [
  {src:'63ee_535-590.mp4',from:15,dur:3,title:'Курсы по ИИ не работают',sub:'и это не вина курсов',zoom:[1.05,1.15],focus:[0.5,0.45]},
  {src:'334e_535-605.mp4',from:8,dur:3.2,focus:[0.3,0.3],zoom:[1.6,1.75],title:'Вечером — урок и промпты'},
  {src:'lubov_02_cafe.jpg',from:0,dur:3.2,focus:[0.3,0.3],title:'Утром — клиенты и пожары',sub:'сотрудники, звонки, заявки'},
  {src:'3e97_85-165.mp4',from:50,dur:3,focus:[0.33,0.3],zoom:[1.5,1.6],title:'Коды откладываются',sub:'…и забываются'},
  {src:'3e97_1000-1035.mp4',from:15,dur:2.6,mode:'full',focus:[0.8,0.95],zoom:[1.15,1.22],title:'Поэтому я не учу'},
  {src:'ffd3_490-530.mp4',from:7.5,dur:3,focus:[0.66,0.4],zoom:[1.2,1.3],title:'Я внедряю за вас',sub:'сайты, автоответы, автопостинг'},
  {src:'3e97_0-20.mp4',from:12.5,dur:3,focus:[0.55,0.5],zoom:[1.02,1.12],title:'Лично или в малой группе',sub:'без кодов и промптов'},
];
const COURSES_P = {...showDefaults, shots: COURSES, endTitle: 'Разберу, что ИИ сделает у вас', endSub: 'бесплатно · 15 минут · это не курс', endPhoto: 'lubov_04_park_coat.jpg'};
const CLAUDE = [
  {src:'lubov2_table_red_low.jpg',from:0,dur:2.8,focus:[0.4,0.3],tag:'ЗНАКОМО?',title:'Таблицы и отчёты — снова ночью?',sub:'а другие уже отдали это Claude'},
  {src:'c1005_table.mp4',from:0,dur:3.2,zoom:[1.0,1.1],focus:[0.6,0.5],tag:'CLAUDE ВЕДЁТ ТАБЛИЦЫ',title:'17 листов с формулами',sub:'сам открыл таблицу и разобрался в ней'},
  {src:'c1005_menu.mp4',from:0,dur:3.8,zoom:[1.0,1.06],focus:[0.5,0.5],title:'Сам выгружает в Excel',sub:'Файл → Скачать → Excel — я только смотрю'},
  {src:'c1005_ans.mp4',from:0,dur:3.8,zoom:[1.0,1.08],focus:[0.3,0.6],title:'И объясняет каждую формулу',sub:'скидки, проценты, бонусы сотрудникам'},
  {src:'lubov2_flat_lipstick.jpg',from:0,dur:3.2,focus:[0.5,0.3],tag:'≈ 2 000 ₽ В МЕСЯЦ',title:'Таблицы, Битрикс24, amoCRM, WB',sub:'предприниматели в России уже ведут это с Claude'},
  {src:'lubov2_flat_jewelry.jpg',from:0,dur:2.8,focus:[0.5,0.3],tag:'БЕЗ РУТИНЫ',title:'Меньше рутины — меньше тревоги',sub:'вы ведёте бизнес, а не таблицы'},
];
const CLAUDE_P = {...showDefaults, shots: CLAUDE, endTitle: 'Покажу и внедрю под вас', endSub: 'это не курс: демонстрация на ваших задачах, лично или в малой группе', cta: 'НАПИШИТЕ «ДЕМОНСТРАЦИЯ»', endPhoto: 'lubov2_hat_lamp.jpg', endDur: 3.8};
export const Root: React.FC = () => (<>
  <Composition id="Reel" component={Reel} durationInFrames={30*12} fps={30} width={1080} height={1920} defaultProps={reelSchemaDefaults} />
  <Composition id="Demo" component={Demo} durationInFrames={30*14} fps={30} width={1080} height={1920} defaultProps={demoDefaults} />
  <Composition id="SkillReel" component={SkillReel} durationInFrames={skillDuration(skillDefaults.shots)} fps={30} width={1080} height={1920} defaultProps={skillDefaults} />
  <Composition id="Showcase" component={Showcase} fps={30} width={1080} height={1920} durationInFrames={showDuration({...showDefaults, shots: SHOTS} as any)} defaultProps={{...showDefaults, shots: SHOTS} as any} />
  <Composition id="Twelve" component={Twelve} fps={30} width={1080} height={1920} durationInFrames={TWELVE_FRAMES} />
  <Composition id="Cover" component={Cover} fps={30} width={1080} height={1920} durationInFrames={1} defaultProps={coverDefaults} />
  <Composition id="Courses" component={Showcase} fps={30} width={1080} height={1920} durationInFrames={showDuration(COURSES_P as any)} defaultProps={COURSES_P as any} />
  <Composition id="CoursesCover" component={Cover} fps={30} width={1080} height={1920} durationInFrames={1} defaultProps={{hook: 'Курсы по ИИ не работают', sub: 'и это не вина курсов', label: 'училка для бизнеса', bg: 'bg_wave.jpg'}} />
  <Composition id="Claude1005" component={Showcase} fps={30} width={1080} height={1920} durationInFrames={showDuration(CLAUDE_P as any)} defaultProps={CLAUDE_P as any} />
  <Composition id="Claude1005Cover" component={Cover} fps={30} width={1080} height={1920} durationInFrames={1} defaultProps={{hook: 'Все уже ведут бизнес с Claude', sub: 'а вы всё ещё руками?', label: 'училка для бизнеса', bg: 'lubov2_table_red_low.jpg'}} />
</>);
