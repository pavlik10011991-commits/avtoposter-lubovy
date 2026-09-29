import React from 'react';
import {Composition} from 'remotion';
import {Reel, reelSchemaDefaults} from './Reel';
import {Demo, demoDefaults} from './Demo';
import {SkillReel, skillDefaults, skillDuration} from './SkillReel';
export const Root: React.FC = () => (<>
  <Composition id="Reel" component={Reel} durationInFrames={30*12} fps={30} width={1080} height={1920} defaultProps={reelSchemaDefaults} />
  <Composition id="Demo" component={Demo} durationInFrames={30*14} fps={30} width={1080} height={1920} defaultProps={demoDefaults} />
  <Composition id="SkillReel" component={SkillReel} durationInFrames={skillDuration(skillDefaults.shots)} fps={30} width={1080} height={1920} defaultProps={skillDefaults} />
</>);
