import React from 'react';
import {Composition} from 'remotion';
import {Reel, reelSchemaDefaults} from './Reel';
import {Demo, demoDefaults} from './Demo';
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
export const Root: React.FC = () => (<>
  <Composition id="Reel" component={Reel} durationInFrames={30*12} fps={30} width={1080} height={1920} defaultProps={reelSchemaDefaults} />
  <Composition id="Demo" component={Demo} durationInFrames={30*14} fps={30} width={1080} height={1920} defaultProps={demoDefaults} />
  <Composition id="SkillReel" component={SkillReel} durationInFrames={skillDuration(skillDefaults.shots)} fps={30} width={1080} height={1920} defaultProps={skillDefaults} />
  <Composition id="Showcase" component={Showcase} fps={30} width={1080} height={1920} durationInFrames={showDuration({...showDefaults, shots: SHOTS} as any)} defaultProps={{...showDefaults, shots: SHOTS} as any} />
</>);
