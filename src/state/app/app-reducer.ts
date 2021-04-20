import { AnyAction, Reducer } from 'redux';
import { actionTypes } from './app-actions';
import * as actions from './app-actions';
import { IAction, IActionReducer } from '../types';

export interface IAppState {
  initialized: boolean;
}

const initialState: IAppState = {
  initialized: false,
};

const reducers: IActionReducer<IAppState> = {
  [actionTypes.INITIALIZE]: (state: IAppState, action: ReturnType<typeof actions.Initialize>) => {
    return {
      ...state,
      userData: action.payload.userData,
    };
  },
};

export const appReducer: Reducer<IAppState, AnyAction> = (state: IAppState = initialState, action: IAction) => {
  const reducer: any = reducers[action.type];
  return reducer ? reducer(state, action) : state;
};
