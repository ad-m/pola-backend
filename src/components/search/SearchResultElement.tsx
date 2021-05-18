import React from 'react';
import styled from 'styled-components';
import { IProductData } from '../../domain/products';
import { padding, color } from '../../styles/theme';

const ListElement = styled.li`
  margin-bottom: ${padding.tiny};
  padding: ${padding.small} ${padding.normal};
  background-color: ${color.border};
`;

const ResultElement = styled.div`
  display: flex;
  flex-flow: column;
  line-height: 1.7em;

  .company {
    text-transform: uppercase;
  }
`;

interface ISearchResultElement {
  product: IProductData;
}

export const SearchResultElement: React.FC<ISearchResultElement> = ({ product }) => (
  <ListElement>
    <ResultElement>
      <span className="company">{product.company?.name || 'No company'}</span>
      <span className="brand">{product.brand?.name || 'No brand'}</span>
      <span className="name">{product.name}</span>
    </ResultElement>
  </ListElement>
);
