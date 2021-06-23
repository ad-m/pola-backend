import React from 'react';
import styled from 'styled-components';
import { SearchInput } from './SearchInput';
import ErrorBoundary from '../../utils/error-boundary';
import { Device, fontSize, color, margin, lineHeight } from '../../styles/theme';
import { TitleSection } from '../../styles/GlobalStyle.css';
import { GooglePlayLink, AppStoreLink } from '../../components/links';
import { urls } from '../../utils/browser/urls';

const Container = styled.div`
  display: flex;
  flex-flow: column;
  width: 100%;
  padding-top: 260px;
  padding-bottom: 70px;
  position: relative;
  text-align: left;

  @media ${Device.mobile} {
    padding: 100px 0 20px 0;
    display: flex;
    align-items: center;
    flex-direction: column;
  }
`;

const Title = styled(TitleSection)`
  font-size: ${fontSize.big};
  text-align: center;
  margin: 0;

  @media ${Device.mobile} {
    width: 100%;
    margin-bottom: ${margin.normal};
  }
`;

const Text = styled.div`
  display: flex;
  flex-flow: column;
  margin: ${margin.small} 0;
  padding: 0;
  font-size: ${fontSize.normal};
  text-align: left;
  line-height: ${lineHeight.normal};
  color: ${color.text.secondary};

  @media ${Device.mobile} {
    text-align: center;
    font-size: ${fontSize.small};
    line-height: ${lineHeight.normal};
  }

  a {
    color: ${color.text.red};
  }
`;

const SearchWrapper = styled.div`
  margin-top: ${margin.normal};
  display: flex;
  flex-flow: column;
  gap: ${margin.small};
  width: 100%;
  max-width: 30rem;

  @media ${Device.desktop} {
    flex-flow: row nowrap;
    justify-content: center;
  }

  .mobile-apps {
    width: 100%;
    max-width: 20rem;
    background-color: red;
    display: flex;
    flex-flow: row nowrap;
    gap: ${margin.small};

    @media ${Device.mobile} {
      margin-top: ${margin.normal};
      justify-content: space-around;
      gap: 0;
    }
  }
`;

interface ISearchForm {
  isLoading: boolean;
  onSearch: (phrase: string) => void;
}

export const SearchForm: React.FC<ISearchForm> = ({ isLoading, onSearch }) => {
  return (
    <ErrorBoundary scope="search-container">
      <Container>
        <Title>Sprawdź informacje o produkcie</Title>
        <Text>
          <span>Wpisz tekst, podyktuj lub zeskanuj kod</span>
          <span>
            Nie znasz kodu?&nbsp;
            <a target="blank" href={urls.external.openFoods.href}>
              Znajdź go w bazie
            </a>
          </span>
        </Text>
        <SearchWrapper>
          <SearchInput onSearch={onSearch} disabled={isLoading} />
          <div className="mobile-apps">
            <AppStoreLink height={48} />
            <GooglePlayLink height={48} />
          </div>
        </SearchWrapper>
      </Container>
    </ErrorBoundary>
  );
};
